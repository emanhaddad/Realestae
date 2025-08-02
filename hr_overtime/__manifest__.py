# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Over time',
    'category': 'HR',
    'author': 'Ayman adam dawood',
    'summary': 'default customization',
    'description': "",
    'depends': [
        'hr_custom',
        'hr_payroll'
    ],
    'data': [
        'security/ir.model.access.csv',

        'views/hr_overtime.xml',
        'views/hr_payroll_overtime_view.xml',
        'views/hr_payslip_view.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
}
