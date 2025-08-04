
import logging,re
import pprint
from werkzeug import urls
from odoo import _, models
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)

class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _get_specific_processing_values(self, processing_values):
        res = super()._get_specific_processing_values(processing_values)
        if self._paystack_is_authorization_pending():
            res['redirect_form_html'] = self.env['ir.qweb']._render(
                self.provider_id.redirect_form_view_id.id,
                {'api_url': self.provider_reference},
            )
        return res

    
    def _get_specific_rendering_values(self, processing_values):
        res = super()._get_specific_rendering_values(processing_values)
        if self.provider_code != 'paystack':
            return res

        base_url = self.provider_id.get_base_url()
        safe_ref = self.reference.replace('/', '-')  # Paystack-friendly
        self.provider_reference = safe_ref  # store for callback validation

        payload = {
            'email': self.partner_email,
            'amount': int(self.amount * 100),
            'reference': safe_ref,
            'callback_url': urls.url_join(base_url, '/payment/paystack/return'),
            "metadata": {
                "custom_fields": [
            {
                "display_name": "Customer Name",
                "variable_name": "customer_name",
                "value": self.partner_name or "Unknown"
            }
        ]
    }
        }
        response = self.provider_id._paystack_make_request('transaction/initialize', payload)
        checkout_url = response['data']['authorization_url']
        return {'redirect_url': checkout_url}
        
    def _get_tx_from_notification_data(self, provider_code, notification_data):
        tx = super()._get_tx_from_notification_data(provider_code, notification_data)
        if provider_code != 'paystack' or len(tx) == 1:
            return tx
        reference = notification_data.get('reference')
        if not reference:
            raise ValidationError("Paystack: " + _("Received data with missing reference."))
        tx = self.search([('provider_reference', '=', reference), ('provider_code', '=', 'paystack')])
        if not tx:
            raise ValidationError("Paystack: " + _("No transaction found matching reference %s.", reference))
        return tx    
        
    def _process_notification_data(self, notification_data):
        super()._process_notification_data(notification_data)
        if self.provider_code != 'paystack':
            return
        reference = notification_data.get('reference') or self.reference
        response = self.provider_id._paystack_make_request(f'transaction/verify/{reference}', method='GET')
        verified_data = response['data']
        self.provider_reference = verified_data['reference']
        status = verified_data['status']
        if status == 'success':
            self._set_done()
        elif status == 'failed':
            self._set_error(_("Payment failed for reference %s.", reference))
        else:
            self._set_pending()


    def _paystack_is_authorization_pending(self):
        return self.filtered_domain([
            ('provider_code', '=', 'paystack'),
            ('state', '=', 'pending'),
            ('provider_reference', 'ilike', 'https'),
        ])
