{
    "name": "Multi Invoice Payment For Customer and Vendor || Multiple Invoice Payment  ",
    "version": "18.0",
    "description": """
        Using this module you can pay multiple invoice payment in one click.
    """,
    'price': 16,
    'currency': 'EUR',
    'license': 'OPL-1',
    "author" : "MAISOLUTIONSLLC",
    'sequence': 1,
    "email": 'apps@maisolutionsllc.com',
    "website":'http://maisolutionsllc.com/',
    'category':"Accounting",
    'summary':"Using this module you can pay multiple invoice payment in one click. Multiple invoice payment in one click for customer",
    "depends": [
        "account",
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/multiinvoice_payment_view.xml'
    ],
    'qweb': [
        # 'static/src/xml/pos_receipt.xml',
    ],
    'css': [],
    'js': [],
    "images": ['static/description/main_screenshot.png'],
    'demo': [],
    'installable': True,
    'auto_install': False,
    'application': True,
}

