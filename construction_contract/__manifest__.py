#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.

{
    'name': 'Constructions Contracts',
    'version': '18.0',
    'license': 'Other proprietary',
    'summary': 'Manage construction vendor contracts',
    'sequence': 25,
    'description': """
Manage Construction Vendor Contracts
=====================================================
TODO

    """,
    'category': 'Services/Project',
    'author': 'Hash IT',
    'website': 'https://hashsd.com',
    'support': 'support@hashsd.com',
    'price': 500,
    'currency': 'EUR',
    'images': [],
    'depends': ['construction_management_app',
                'base',
                'project_task_material_requisition',
                'cash_request',
                'portal',
                'utm'],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Views
        'views/construction_contract_views.xml',
        'views/construction_receipt.xml',
        'views/project_views.xml',
        'views/res_config_settings.xml',
        'wizard/construction_contract_reject_views.xml',
        #Reports
        'reports/receipt_report_template.xml',
        'reports/receipt_report_views.xml',
        'reports/final_receipt_report_template.xml',

    ],
    'demo': [
    ],
    'qweb': [
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
}
