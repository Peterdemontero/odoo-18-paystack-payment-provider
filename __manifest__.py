
{
    'name': 'Paystack Payment Provider',
    'summary': 'Payment Provider: Custom Paystack Implementation v2.0',
    'author': 'Peter Demontero',
    'version': '2.0',
    'category': 'Accounting/Payment Providers',
    'depends': ['payment'],
    'data': [
        'views/payment_paystack_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
        'data/payment_method_data.xml',
        'data/cron.xml',
        'views/paystack_transactions.xml',
    ],
    'assets': {
        'web.assets_frontend': [
            'payment_paystack/static/src/js/payment_alert_hide.js',
        ],
    },
    'images': ['static/description/icon.png'],
    'installable': True,
    'application': False,
    'license': 'LGPL-3'
}
