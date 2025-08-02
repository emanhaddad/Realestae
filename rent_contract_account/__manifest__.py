

{
    'name': 'Rent Contract Account',
    'summary': """
        This module extends the Rent Contract module to integrate with accounting.""",
    'version': '18.0',
    'author': 'App Script',
    'depends': ['rent_contract','account'
    ],
    'data': [
  
        #Views
            'views/real_estate.xml',
            'views/res_config_settings_views.xml',
       
    ],
}
