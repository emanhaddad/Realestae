{
    'name': 'Cash Order',
    'version': '18.1',
    'author': 'App-Script For Software',
    'category': ' ',
    'sequence': 10,
    'summary': 'cash order',
    'description': """
""",
    'website': ' ',
    'depends': ['base', 'hr','account' , 'mail'],
    'data': [
        'security/groups.xml',
        'security/ir.model.access.csv',
        'views/hr_view.xml',
        'views/cash_request_view.xml',
        'views/beneficiary.xml',
        'reports/cash_order_report.xml',
        'reports/cash_order_report_view.xml',
        'reports/cash_receive_report.xml',
        'views/views.xml',
        'views/cash_receive_view.xml',
    ],
    'test': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
