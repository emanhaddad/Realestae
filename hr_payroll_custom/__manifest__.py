# -*- coding:utf-8 -*-

{
    'name': 'Odoo 14 HR Payroll',
    'category': 'Generic Modules/Human Resources',
    'version': '18.0.8.0.0',
    'sequence': 1,
    'license': 'LGPL-3',
    'summary': 'Payroll For Odoo 14 Community Edition',
    'description': "",
    'website': 'http://www.app-script.com/',
    'depends': [
        'hr_payroll',
        'report_xlsx'
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/hr_contract_views.xml',
        'views/hr_salary_rule_views.xml',
        'views/bonus_views.xml',
        'views/payslip_view.xml',
        'report/reports_actions.xml',
    ],
    'application': True,
}
