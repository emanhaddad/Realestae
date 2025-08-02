# -*- coding: utf-8 -*-
##############################################################################
#
#
##############################################################################

{
    'name': 'Violation - Punishment',
    'version': '18.0',
    'author': '',
    'category': 'Human Resources',
    'website': '',
    'summary': 'Employee Violation and Punishment',
    'description': """

Employee Violation and Punishment
==========================

    """,
    'depends': ['hr_custom','hr_payroll'],
    'data': [
    'security/ir.model.access.csv',
    'views/hr_violation_punishment_view.xml',
    'views/hr_employee_view.xml',
    ],
    'demo': [],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
