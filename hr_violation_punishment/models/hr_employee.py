# -*- coding: utf-8 -*-
##############################################################################
#
#    
#    
#
##############################################################################

from odoo import api, fields, models, _


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    emp_violation_ids = fields.One2many('hr.violation.punishment', 'employee_id', string='Employee Violation', readonly=True)


