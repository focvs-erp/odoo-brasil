{
    'name': "Método de Pagamento Trustcode",
    'summary': "Payment Acquirer: Iugu Implementation",
    'description': """Iugu payment gateway for Odoo.""",
    'author': "Danimar Ribeiro",
    'category': 'Accounting',
    'version': '13.0.1.0.0',
    'depends': ['account', 'payment', 'sale'],
    'external_dependencies': {
        'python': ['iugu'],
    },
    'data': [
        'views/payment_views.xml',
        'views/iugu.xml',
        'views/redirect_message.xml',
        'views/static_template.xml',
        'data/iugu.xml',
    ],
    'application': True,
    'sequence': 10
}
