

{
    'name': 'Real estate Inspection',
    'summary': """
        This module extends the Real estate module allowing the Real estate inspections.""",
    'version': '18.0',
    'author': 'App Script',
    'depends': ['real_estate','rent_contract',],
    'data': [
        #Security
            'security/real_estate_inspection.xml',
            'security/ir.model.access.csv',
        #Views
            'views/real_estate.xml',
            'views/real_estate_inspection_line.xml',
            'views/real_estate_inspection_item.xml',
            'views/real_estate_inspection.xml',
        #Data
            'data/real_estate_inspection.xml',
    ],
    'demo': [
        'demo/real_estate_inspection.xml',
    ],
}
