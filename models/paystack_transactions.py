from datetime import datetime
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError
import logging

_logger = logging.getLogger(__name__)

class PaystackTransaction(models.Model):
    _name = 'paystack.transaction'
    _description = 'Paystack Transactions'
    _order = 'transaction_date desc'

    reference = fields.Char('Reference', required=True, readonly=True)
    amount = fields.Float('Amount', required=True, readonly=True)
    status = fields.Selection([
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('pending', 'Pending')
    ], 'Status', readonly=True)
    customer_name = fields.Char('Customer Name', readonly=True)
    customer_email = fields.Char('Customer Email', readonly=True)
    transaction_date = fields.Datetime('Transaction Date', readonly=True)
    raw_data = fields.Text('Raw Data', readonly=True)

    _sql_constraints = [
        ('reference_unique', 'unique(reference)', 'This transaction already exists!')
    ]


    from odoo import models, api
from odoo.exceptions import ValidationError
import json, logging

class PaystackTransaction(models.Model):
    _name = 'paystack.transaction'
    _description = 'Paystack Transactions'
    _order = 'transaction_date desc'

    reference = fields.Char('Reference', required=True, readonly=True)
    amount = fields.Float('Amount', readonly=True)
    fees = fields.Float('Fees', readonly=True)
    currency = fields.Char('Currency', readonly=True)
    channel = fields.Char('Payement Method', readonly=True)
    status = fields.Selection([
    ('success', 'Success'),
    ('failed', 'Failed'),
    ('pending', 'Pending'),
    ('abandoned', 'Abandoned'),
    ('reversed', 'Reversed'),
    ('processing', 'Processing'),
], 'Status', readonly=True)
    customer_name = fields.Char('Customer Name', readonly=True)
    customer_email = fields.Char('Customer Email', readonly=True)
    transaction_date = fields.Datetime('Transaction Date', readonly=True)
    raw_data = fields.Text('Raw Data', readonly=True)

    _sql_constraints = [
        ('reference_unique', 'unique(reference)', 'This transaction already exists!')
    ]

    @api.model
    def action_fetch_transactions(self):
        """Fetch transactions from Paystack API and update/create records"""
        try:
            # Get Paystack provider
            provider = self.env['payment.provider'].search([('code', '=', 'paystack')], limit=1)
            if not provider or not provider.paystack_secret_key:
                raise ValidationError("Paystack provider is not configured with a secret key.")
            
            # Call Paystack API
            response = provider._paystack_make_request('transaction', method='GET')
            transactions = response.get('data', [])
            if not transactions:
                raise ValidationError("No transactions found from Paystack.")

            for tx in transactions:
                vals = {
                    'reference': tx.get('reference'),
                    'amount': float(tx.get('amount') or 0) / 100.0,  # Convert from kobo
                    'status': tx.get('status'),
                    'fees': float(tx.get('fees') or 0) / 100.0,
                    'currency': tx.get('currency', 'GHS'),
                    'channel': tx.get('channel'),
                    'customer_email': tx.get('customer', {}).get('email'),
                    'customer_name': tx.get('metadata', {}).get('custom_fields', [{}])[0].get('value', 'Unknown'),
                    'transaction_date': self._convert_date(tx.get('paid_at') or tx.get('created_at')),
                    'raw_data': json.dumps(tx, indent=2)
                }
                existing = self.search([('reference', '=', vals['reference'])], limit=1)
                if existing:
                    existing.write(vals)
                else:
                    self.create(vals)

        except Exception as e:
            logging.exception("Error fetching Paystack transactions")
            raise ValidationError(f"Failed to sync Paystack transactions: {str(e)}")
        return True
    
    def _convert_date(self, date_str):
        """Convert Paystack's ISO8601 date to Python datetime"""
        if not date_str:
            return False
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ"):
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        return False
