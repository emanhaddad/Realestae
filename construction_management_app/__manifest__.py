# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Construction Management',
    'version': '18.8.2',
    'price': 55.0,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'author': 'Probuse Consulting Service Pvt. Ltd.',
    'website': 'https://www.probuse.com',
    'support': 'contact@probuse.com',
    'images': ['static/description/img1.jpg'],
    'category': 'Services/Project',
    'live_test_url': 'http://probuseappdemo.com/probuse_apps/construction_management_app/410',#'https://youtu.be/M5Nk6jD7-ao',
    'summary':  """This module provide Construction Management Related Activity.""",
    'description': """
This module provide Construction Management Related Activity.
Construction
Construction Projects
Budgets
Notes
Materials
Material Request For Job Orders
Add Materials
Job Orders
Create Job Orders
Job Order Related Notes
Issues Related Project
Vendors
Vendors / Contractors

Construction Management
Construction Activity
Construction Jobs
Job Order Construction
Job Orders Issues
Job Order Notes
Construction Notes
Job Order Reports
Construction Reports
Job Order Note
Construction app
Construction 
job costing
job cost sheet
job contracting
Construction Management

This module provide feature to manage Construction Management activity.
Menus:
Construction
Construction/Configuration
Construction/Configuration /Stages
Construction/Construction
Construction/Construction/Budgets
Construction/Construction/Notes
Construction/Construction/Projects
Construction/Job Orders
Construction/Job Orders /Issues
Construction/Job Orders /Job Orders
Construction/Job Orders /Notes
Construction/Materials / BOQ
Construction/Materials /Material Requisitions / BOQ
Construction/Materials /Materials
Construction/Vendors
Construction/Vendors /Contractors
Defined Reports
Notes
Project Report
Task Report
Construction Project - Project Manager
real estate property
propery management
bill of material
Material Planning On Job Order

Bill of Quantity On Job Order
Bill of Quantity construction
    """,
    'depends': ['project', 'stock', 'stock_account',
                'purchase', 'material_purchase_requisitions', 'project_task_material_requisition',
                'hr_timesheet', 'note',
                # 'project_issue', 'odoo_account_budget',
                ],
    'data': [
        'security/construction_security.xml',
        'security/ir.model.access.csv',
        'wizard/project_user_subtask_view.xml',
        'views/construction_management_view.xml',
        # 'wizard/purchase_order_view.xml',
        'views/project_task_view.xml',
        'views/project_view.xml',
        'views/note_view.xml',
        'views/report_noteview.xml',
        'views/report_reg.xml',
        'views/project_report.xml',
        'views/project_task_view.xml',
        'views/task_report.xml',
        # 'views/purchase_view.xml',
        # 'views/stock_picking.xml',
        'views/product_view.xml',
        'views/purchase_requisition_view.xml',
        'views/res_config_settings.xml',
    ],
    'installable' : True,
    'application' : False,
    'auto_install' : False,
}
