# -*- coding: utf-8 -*-
##############################################################################
#		App-script Business Solutions
#
##############################################################################

from odoo import fields, models, api, exceptions, _
import time
from datetime import datetime
from odoo.exceptions import ValidationError ,UserError
from dateutil import relativedelta
import math

class RestructureWiz(models.TransientModel):
	_name = "restructure.loan.wiz"
	
	loan_id = fields.Many2one('hr.loan', string='Loan Type', readonly=True,store=True)
	remain_amount = fields.Float(string="Remain Amount", readonly=True,store=True)
	payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today())
	partial_amount_paid = fields.Float('Amount To pay')
	installment = fields.Integer(string="No Of Installments", required=True, default=1)
	installment_amount = fields.Float(string="Installment Amount")
	journal_id = fields.Many2one('account.journal', string="Journal")
	dircet_payment_date = fields.Date(string="Payment Start Date", required=True, default=fields.Date.today())

	@api.onchange('installment','partial_amount_paid')
	def onchange_installment(self):
		if not self.loan_id:
			return
		if self.partial_amount_paid:
			remine = self.remain_amount - self.partial_amount_paid
			self.installment_amount = remine /  self.installment
		else:
			self.installment_amount = self.remain_amount /  self.installment


	def restructure(self):
		for rec in self.loan_id.loan_arc_ids:
			if rec.state in ['paid','draft']:
				rec.unlink()
			else:
				pass
		self.loan_id.write({
			'payment_date' : self.payment_date,
			'installment' : self.installment,
			'installment_amount' : self.installment_amount,
			'total_paid_amount': self.loan_id.total_paid_amount + self.partial_amount_paid,
			'remain_amount' : self.remain_amount - self.partial_amount_paid,
			'restructure' : _(str(datetime.today()))
			})
		self.compute_installment()

		if self.partial_amount_paid:
			self._partial_amount_paid()

	def compute_installment(self):		
		num=1
		date_start = datetime.strptime(str(self.payment_date), '%Y-%m-%d')
		amount = self.installment_amount
		if self.loan_id.loan_id.decimal_calculate == 'without':
			if not amount.is_integer():
				num=2
				frac, whole = math.modf(amount)
				decimal_amount = frac * self.installment
				decimal_amount += whole
				amount=whole
				arch = self.env['hr.loan.archive'].create({
					'date': date_start,
					'year': date_start.year,
					'month': date_start.month,
					'amount': decimal_amount,
					'employee_id': self.loan_id.employee_id.id,
					'loan_type_id': self.loan_id.loan_id.id,
					'loan_id': self.loan_id.id
				})
				if self.loan_id.state == 'paid':
					arch.write({'state': 'paid'})
				date_start = date_start + relativedelta.relativedelta(months=+1)
		if amount != 0:
			for i in range(num, self.installment + 1):
				arch = self.env['hr.loan.archive'].create({
					'date': date_start,
					'year': date_start.year,
					'month': date_start.month,
					'amount': amount,
					'employee_id': self.loan_id.employee_id.id,
					'loan_type_id': self.loan_id.loan_id.id,
					'loan_id': self.loan_id.id})

				if self.loan_id.state == 'paid':
					arch.write({'state': 'paid'})
				date_start = date_start + relativedelta.relativedelta(months=+1)
		return True

	def _partial_amount_paid(self):

		if not self.loan_id.loan_id.loan_account_id:
			raise UserError(_("Please specify Debit account in Selected Loan Type"))
		if not self.journal_id.payment_debit_account_id:
			raise UserError(_("Please specify journal payment credit account "))
		new_payment_id = self.env['hr.loan.payment'].create({
			'employee_id': self.loan_id.employee_id.id,
			'loan_type_id': self.loan_id.loan_id.id,
			'loan_id': self.loan_id.id,
			'loan_code': self.loan_id.name,
			'date': self.loan_id.date,
			'loan_amount': self.loan_id.loan_amount,
			'remain_amount': self.remain_amount,
			'date': self.payment_date,
			'payment_type':'partial',
			'installment_type': 'reduce',
			'amount': self.partial_amount_paid,
			'journal_id': self.journal_id.id,
			'state': 'paid'
			})


		new_arc_id = self.env['hr.loan.archive'].create({
			'date': self.loan_id.date,
			'year': datetime.strptime(str(self.loan_id.date), '%Y-%m-%d').year,
			'month': datetime.strptime(str(self.loan_id.date), '%Y-%m-%d').month,
			'amount': self.partial_amount_paid,
			'employee_id': self.loan_id.employee_id.id,
			'loan_type_id': self.loan_id.loan_id.id,
			'loan_id': self.loan_id.id,
			'payment_type':'direct_payment',
			'state': 'done'
			})

		new_payment_id.create_move(self.partial_amount_paid)  
		new_arc_id.action_done() 
