# Part of Odoo. See LICENSE file for full copyright and licensing details.

import hmac
import hashlib
import json
import logging
import pprint

from werkzeug.exceptions import Forbidden

from odoo import http
from odoo.exceptions import ValidationError
from odoo.http import request

_logger = logging.getLogger(__name__)


class PaystackController(http.Controller):
    _return_url = '/payment/paystack/return'
    _webhook_url = '/payment/paystack/webhook'

    @http.route(_return_url, type='http', methods=['GET'], auth='public')
    def paystack_return_from_checkout(self, **data):
        """ Process the notification data sent by Paystack after redirection from checkout.

        :param dict data: The query string data (e.g., reference, status).
        """
        _logger.info("Handling redirection from Paystack with data:\n%s", pprint.pformat(data))

        # Handle the notification data only if not cancelled.
        if data.get('status') != 'cancelled':
            request.env['payment.transaction'].sudo()._handle_notification_data('paystack', data)
        else:
            # The customer canceled the payment.
            pass

        # Redirect to payment status page
        return request.redirect('/payment/status')

    @http.route(_webhook_url, type='http', methods=['POST'], auth='public', csrf=False)
    def paystack_webhook(self):
        """ Process the notification data sent by Paystack to the webhook.

        :return: An empty string to acknowledge the notification.
        :rtype: str
        """
        data = request.get_json_data()
        _logger.info("Notification received from Paystack with data:\n%s", pprint.pformat(data))

        if data.get('event') == 'charge.success':
            try:
                # Locate the transaction
                tx_sudo = request.env['payment.transaction'].sudo()._get_tx_from_notification_data(
                    'paystack', data['data']
                )

                # Verify the webhook signature
                signature = request.httprequest.headers.get('x-paystack-signature')
                self._verify_notification_signature(signature, request.httprequest.data, tx_sudo)

                # Handle the notification
                tx_sudo._handle_notification_data('paystack', data['data'])
            except ValidationError:
                _logger.exception("Unable to handle Paystack webhook data; skipping to acknowledge.")
        return request.make_json_response('')

    @staticmethod
    def _verify_notification_signature(received_signature, raw_body, tx_sudo):
        """ Verify the Paystack webhook signature.

        :param str received_signature: The signature sent by Paystack in the header.
        :param bytes raw_body: The raw request body.
        :param recordset tx_sudo: The sudoed transaction referenced by the notification data.
        :return: None
        :raise Forbidden: If the signature is invalid.
        """
        if not received_signature:
            _logger.warning("Received Paystack webhook with missing signature.")
            raise Forbidden()

        expected_secret = tx_sudo.provider_id.paystack_webhook_secret
        expected_signature = hmac.new(
            expected_secret.encode('utf-8'),
            raw_body,
            hashlib.sha512
        ).hexdigest()

        if not hmac.compare_digest(received_signature, expected_signature):
            _logger.warning("Received Paystack webhook with invalid signature.")
            raise Forbidden()
