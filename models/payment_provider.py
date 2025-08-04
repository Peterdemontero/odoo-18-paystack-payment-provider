import requests
from odoo import _, fields, models
from odoo.exceptions import ValidationError
# from odoo.addons.payment_paystack import const


class PaymentProvider(models.Model):
    _inherit = 'payment.provider'

    # Add Paystack to the existing 'code' field (not 'provider')
    code = fields.Selection(
        selection_add=[('paystack', "Paystack")],
        ondelete={'paystack': 'set default'}
    )

    paystack_secret_key = fields.Char(
        string="Paystack Secret Key",
        groups='base.group_system'
    )
    paystack_webhook_secret = fields.Char(
        string="Paystack Webhook Secret",
        groups='base.group_system'
    )
    paystack_public_key = fields.Char(
        string="Paystack Public Key",
        groups='base.group_system'
    )

   
    def _paystack_make_request(self, endpoint, payload=None, method='POST'):
        """Make API request to Paystack."""
        self.ensure_one()
        url = f"https://api.paystack.co/{endpoint}"
        headers = {
            'Authorization': f"Bearer {self.paystack_secret_key}",
            'Content-Type': 'application/json',
        }
        if method == 'POST':
            response = requests.post(url, json=payload, headers=headers, timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)

        # Log full response for debugging
        try:
            result = response.json()
        except Exception:
            result = response.text
        if response.status_code != 200:
            raise ValidationError(f"Paystack error {response.status_code}: {result}")
        if not result.get('status'):
            raise ValidationError(_("Paystack error: %s") % result.get('message'))
        return result
    
    def _get_default_payment_method_codes(self):
        """Ensure Paystack providers always get a default payment method."""
        default_codes = super()._get_default_payment_method_codes()
        if self.code == 'paystack':
            return ['paystack']
        return default_codes
    
    # def _get_default_payment_method_id(self):
    #     """Set default payment method for Paystack."""
    #     self.ensure_one()
    #     if self.code != 'paystack':
    #         return super()._get_default_payment_method_id()
    #     return self.env.ref('payment_paystack.payment_method_paystack').id