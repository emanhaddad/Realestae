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
	


	loans_arc_ids =  fields.One2many('hr.loan.archive','payslip_id',string='Loan Lines',)

	def compute_sheet(self):
		
		for rec in self :
			clause_1 = ['&', ('date', '<=', rec.date_to), ('date', '>=', rec.date_from)]
			# OR if it starts between the given dates
			clause_2 = ['&', ('date', '<=', rec.date_to), ('date', '>=', rec.date_from)]
			# OR if it starts before the date_from and finish after the date_to (or never finish)
			clause_3 = ['&', ('date', '<=', rec.date_from), '|', ('date', '=', False), ('date', '>=', rec.date_to)]
			clause_final = [('loan_id.contract_id', '=', rec.contract_id.id),('employee_id', '=', rec.employee_id.id),('state', '=','paid'), '|', '|'] + clause_1 + clause_2 + clause_3
			loans_arc = self.env['hr.loan.archive'].search(clause_final)

			rec.loans_arc_ids = loans_arc
		super(HrPayslip, self).compute_sheet()
		
		return True

	def action_payslip_done(self):
		super(HrPayslip, self).action_payslip_done()
		self.loans_arc_ids.state = 'done'



