

{
    'name': 'Real estate Expenses Account',
    'summary': """
        This module extends the Real Estate Expenses module to integrate with accounting.""",
    'version': '18.0',
    'author': 'App Script',
    'depends': ['real_estate_expenses','rent_contract_account'],
    'data': [
        #Security
            'security/real_estate_expenses.xml',
        #Views
            'views/real_estate.xml',
            # 'views/real_estate_expenses.xml',
            'views/res_config_settings_views.xml',
       
    ],
}
