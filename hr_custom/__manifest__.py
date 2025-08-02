# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Custom',
    'category': 'HR',
    'author': 'Ayman adam dawood',
    'summary': 'default customization',
    'description': "",
    'depends': ['hr' , 'hr_contract'],
    'data': [
        'security/ir.model.access.csv',

        'views/hr_employee_view.xml',
        'views/hr_employee_family_view.xml',
        'views/hr_contract.xml',
        'views/employee_form_report.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
}
