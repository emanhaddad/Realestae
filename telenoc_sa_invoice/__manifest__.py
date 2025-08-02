{
    'name': 'Telenoc K.S.A - Invoice | Saudi Electronic Invoice | QR Code | E-Invoice | Tax Invoice | Saudi VAT Invoice',
    'summary': 'TeleNoc E-Invoice is fully compatible with Odoo standard invoice template.',
    'version': '18.0.1.0.0',
    'author': 'Odoo Team, Telenoc',
    'website': 'http://www.telenoc.org/',
    'category': 'Accounting/Localizations',
    'license': 'LGPL-3',
    'description': """
        Invoices for the Kingdom of Saudi Arabia
    """,
    'depends': [
        'l10n_sa', 
        'telenoc_e_invoice'
    ],
    'data': [
        'views/view_move_form.xml',
        'views/report_invoice.xml',
    ],
    'images': [
        'static/description/banner.jpg',
        'static/description/apps_screenshot.jpg'
    ],
}
