# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

{
    'name': 'HR Holidays',
    'category': 'HR',
    'author': 'Ayman adam dawood',
    'summary': 'default customization',
    'description': "",
    'depends': ['hr_holidays' , 'hr_custom',"hr_payroll_custom"],
    'data': [
        'data/cron_job.xml',

        'views/hr_leave_type_view.xml',
        'views/hr_employee_view.xml',
        'views/bonus_views.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'auto_install': True,
}
