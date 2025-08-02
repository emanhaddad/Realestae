# -*- coding: utf-8 -*-
{
    'name': "Real Estate",

    'summary': """
        This is real estate module for managing assets and beneficieries""",

    'description': """
        This is real estate module for managing assets and beneficieries
    """,

    "author": "App Script",

    
    'category': 'Assets',
    'version': '18.1',

    # any module necessary for this one to work correctly
    'depends': ['base','hr',
    'project',
    'account'
    ],

    # always loaded
    'data': [
        #Security
            'security/realestate_sequrity_view.xml',
            'security/ir.model.access.csv',
            'data/sequence.xml',
        #Views
            'views/real_estate_view.xml',
            'views/real_estate_units_view.xml',
            'views/res_partner_view.xml',
            'views/hr_employee_form_view_inheritance.xml',
            'views/property_evaluation.xml',
            'views/real_estate_configuration.xml',
            'views/res_config_settings_views.xml',
    ],

    'installable':True,
    'auto_install':True,
    'application':True,
}
