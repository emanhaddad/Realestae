# -*- coding: utf-8 -*-
##############################################################################
#
#    App-script Business Solutions
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from datetime import date, datetime, timedelta
from dateutil import relativedelta
import math

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'
    
    overtime_ids = fields.One2many(
        string="HR Overtime",
        comodel_name="hr.payroll.overtime.line",
        inverse_name="payslip_id",
    )
    
    def compute_sheet(self):
        for rec in self :	
            clause = [
            ('payroll_date', '<=', rec.date_to), 
            ('payroll_date', '>=', rec.date_from),
            ('employee_id', '=', rec.employee_id.id),
            ('state', '=','waiting')
        ]
        
            overtime_arc = self.env['hr.payroll.overtime.line'].search(clause)

            rec.overtime_ids = overtime_arc
        super(HrPayslip, self).compute_sheet()

        return True

    def action_payslip_done(self):
        super(HrPayslip, self).action_payslip_done()
        self.overtime_ids.state = 'done'
        #self.overtime_ids.line_ids.state = 'done'
