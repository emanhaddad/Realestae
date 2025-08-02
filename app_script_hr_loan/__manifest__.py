# -*- coding: utf-8 -*-

{
    "name": "Loans Management",
    "version": "18.0",
    "category": "Generic Modules/HR",
    "description": """ Manage Loan Requests

    """,
    "author": "app-script",
    "website": "http://app-script.com",
    "depends":["hr","hr_payroll",'account'],
    "data": [
        "security/hr_loan_security.xml",
        'security/ir.model.access.csv',
        
        "data/hr_loan_seq.xml",
         'data/hr_loan_data.xml',
    	"views/hr_loan_view.xml",
        "views/hr_loan_payment_view.xml",
        "views/hr_payslip_view.xml",
        'wizard/restructuring_wizard_view.xml',
        "reports/employee_loan_report.xml",
        "reports/report_action.xml"

    ],
    'images': ['static/description/banner.png'],
    "installable": True,
    "active": True,
    'currency': 'EUR',
    'price': '300'
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:

