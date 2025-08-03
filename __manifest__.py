
{
    'name': 'Paystack Payment Acquirer',
    'summary': 'Payment Provider: Custom Paystack Implementation',
    'author': 'Peter Demontero',
    'version': '1.0',
    'category': 'Accounting/Payment Providers',
    'depends': ['payment'],
    'data': [
        'views/payment_paystack_templates.xml',
        'views/payment_provider_views.xml',
        'data/payment_provider_data.xml',
        'data/payment_method_data.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'images': ['static/description/icon.png'], 
}
