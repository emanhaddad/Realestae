

{
    'name': 'Real estate Expenses',
    'summary': """
        This module extends the Real estate module allowing the Real estate Expenses.""",
    'version': '18.0',
    'author': 'App Script',
    'depends': ['rent_contract','real_estate'],
    'data': [
        #Security
            'security/real_estate_expenses.xml',
            'security/ir.model.access.csv',
        #Views
            'views/real_estate.xml',
            'views/real_estate_expenses.xml',
        #Data
            'data/real_estate_expenses.xml',
    ],
    'demo': [
        #'demo/real_estate_expenses.xml',
    ],
}
