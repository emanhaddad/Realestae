# -*- coding: utf-8 -*-
{
    'name': "Rent Contract",

    'summary': """
        Manage Contracts and track payments""",

    'author': "App Script",
    
    'category': 'Uncategorized',
    'version': '18.1',

    'depends': ['real_estate', 'web','product'],

    # always loaded
    'data': [
        #Security
            'security/rent_contract_security.xml',
            'security/ir.model.access.csv',
        #Data
            'data/contracts_seq.xml',
            'data/rent_contract_seq.xml',
            'data/contract_cron.xml',
        #Views
            #'views/expired_contract_alert_view.xml',
            #'views/account_analytic_contract_view.xml',
            'views/realestate_contract_view.xml',
            'views/product_view.xml',
            'views/res_partner_view.xml',
            'views/dashboard_payment_alert.xml',

            #'views/real_estate_view.xml',
            #'views/real_estate_units_view.xml',
    ],
}
