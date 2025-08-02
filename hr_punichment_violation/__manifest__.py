# -*- coding: utf-8 -*-
##############################################################################
#
#    NCTR, Nile Center for Technology Research
#    Copyright (C) 2022-2023 NCTR (<http://www.nctr.sd>).
#
##############################################################################

{
    "name": "HR punichment & violation Features",
    "version": "18.1",
    "category": "Human Resources",
    "description": """Manage punichment & violation in company""",
    "website": "http://www.app-script.com/",
    "depends": ["hr_custom",'hr_payroll_custom'],
    "data": ['security/ir.model.access.csv',
             'data/hr_payroll_data.xml',
             'views/hr_penalty_view.xml',
             'views/hr_violation_view.xml',
             'views/hr_employee_violation_view.xml',
             ],

    'license': 'LGPL-3',
}
