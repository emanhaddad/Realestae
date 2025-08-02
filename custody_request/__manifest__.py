{
    'name': 'Custody Request',
    'version': '18.0',
    'license': 'OPL-1',
    'category': 'Accounting',
    'author': 'SGT',
    'support': 'info@softguidetech.com',
    'website': 'https://softguidetech.com',
    'data': [

        'security/security_view.xml',
        'security/ir.model.access.csv',
        'views/configure_view.xml',
        'views/custody_approval_route.xml',
        'views/custody_request_view.xml',
        #'data/custody_approval_route.xml',
        #'views/res_config_settings_views.xml',
        'reports/custody_report.xml',
    ],
    'images': [
        'static/description/logo.gif',
    ],
    'depends': ['base','account','analytic','purchase','cash_request'],




    'installable': True,
    'application': True,






}
