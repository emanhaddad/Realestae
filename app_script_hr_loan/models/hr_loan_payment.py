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

class LoanPayment(models.Model):

	_name ='hr.loan.payment'
	_inherit = ['mail.thread']
	_description = "Loans Payment"
	_order = "date desc, id desc"

	def _default_employee(self):
		return self.env.context.get('default_employee_id') or self.env['hr.employee'].search([('user_id', '=', self.env.uid)], limit=1)
		
	name =  fields.Char("Name", readonly=True)
	date = fields.Date("Payment Date", default=fields.datetime.now(), required=True, readonly=True,
		)
		
	loan_type_id = fields.Many2one('hr.loan.type', string='Loan Type', required=True, readonly=True,
		states={'draft': [('readonly', False)]})
	loan_code = fields.Char(related="loan_type_id.code", string="Loan code", store=True)    
	loan_date = fields.Date(related="loan_id.payment_date", string="Loan Date", store=True)
	loan_amount = fields.Float(related="loan_id.loan_amount", string="Loan Amount", store=True)
	employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
	loan_id = fields.Many2one('hr.loan', 'Loan', required=True, readonly=True)
	remain_amount = fields.Float(string='Remain Amount')
	amount = fields.Float("Amount" )
	note = fields.Text("Notes")  
	arc_ids = fields.Many2many('hr.loan.archive', string='Payment Installments') 
	state = fields.Selection([
		('draft','Draft') ,
		('requested','Requested'),
		('transfered','Transfered'),
		('paid','Paid')
		],string='Status', readonly=True, copy=False, index=True, tracking=True, default='draft')
	payment_type = fields.Selection([
	   ('partial','Partial') , 
	   ('all','All')
	   ], string='Payment Type', required=True, readonly=True,
		states={'draft': [('readonly', False)]},default='partial')
	installment_type = fields.Selection([
		('pay','Pay Installments'),
		('reduce','Reduce Installments')
		], string='Installment Payment Type',readonly=True,
		states={'draft': [('readonly', False)]}, required=False)
	company_id = fields.Many2one('res.company' , default=lambda self: self.env.user.company_id) 
	journal_id = fields.Many2one('account.journal', string="Journal",required=True)   

	@api.model
	def create(self, vals):
		if not vals.get('name', False):
			vals['name'] = self.env['ir.sequence'].next_by_code('hr.loan.payment') or '/'
		if vals.get('loan_id',False):
			vals['remain_amount'] = self.env['hr.loan'].browse(vals['loan_id']).remain_amount
		return super(LoanPayment, self).create(vals)

	
	def write(self, vals):
		if vals.get('loan_id',False):
			vals['remain_amount'] = self.env['hr.loan'].browse(vals['loan_id']).remain_amount
		return super(LoanPayment, self).write(vals)

	@api.onchange('loan_id')
	def _onchange_loan_id(self):
		for rec in self:
			rec.remain_amount = rec.loan_id.remain_amount

	@api.onchange('employee_id')
	def _onchange_employee_id(self):
		loan_ids = self.env['hr.loan'].search([
			('employee_id','=',self.employee_id.id),
			('state','=','paid')
		])
		loan_list = []
		for loan_id in loan_ids:
			loan_list.append(loan_id.loan_id.id)
		loan_list = list(set(loan_list))
		print('loan list is : ', loan_list)
		return {'domain': {'loan_type_id': [('id', 'in', loan_list)]}} 

	
	def unlink(self):
		for payment in self:
			if payment.state not in ('draft'):
				raise UserError(_('You cannot delete a Record which is not in draft state.'))
		return super(LoanPayment, self).unlink()

	
	def action_request(self):
		self.write({'state':'requested'})
		
	
	def action_transfer(self):
		for payment in self:
			amount = payment.amount
			if payment.payment_type == 'all':
				amount = payment.remain_amount
			else:
				if payment.installment_type == 'pay':
					amount = sum(payment.mapped('arc_ids.amount')) 			
			self.action_payment()

	
	def action_draft(self):
		self.write({'state':'draft'})

	
	def action_payment(self):
		for payment in self:
			if not self.loan_id.loan_id.loan_account_id:
				raise UserError(_("Please specify Debit account in Selected Loan Type"))

			if not self.journal_id.payment_debit_account_id:
				raise UserError(_("Please specify journal payment credit account "))

			if payment.payment_type == 'all':
				arc_ids = payment.loan_id.loan_arc_ids.filtered(lambda arch: arch.state == 'paid')
				arc_ids.write({'payment_type':'direct_payment','date':fields.Date.today()})
				arc_ids.action_done()
				amount = 0.0
				for arc in arc_ids:
					amount += arc.amount
				payment.create_move(amount)

			else:
				if payment.installment_type == 'pay':
					payment.arc_ids.write({'payment_type':'direct_payment'})
					payment.arc_ids.action_done()
					amount = 0.0
					for arc in payment.arc_ids:
						amount += arc.amount
					payment.create_move(amount)
					
				else:
					remain_amount = payment.remain_amount - payment.amount
					arc_ids = payment.loan_id.loan_arc_ids.filtered(lambda arch: arch.state == 'paid')
					installment = len(arc_ids)
					installment_amount = remain_amount / installment
					frac, integ = math.modf(installment_amount)
					decimal_amount = frac * installment
					decimal_amount += integ
					_amount = integ
					num = 1
					for arc in arc_ids:
						if num == 1:
							arc.write({'amount':decimal_amount})
							num += num
						else:
							arc.write({'amount':_amount})
					date_start = datetime.strptime(str(payment.date), '%Y-%m-%d')
					new_arc_id = self.env['hr.loan.archive'].create({
					    'date': date_start,
					    'year': date_start.year,
					    'month': date_start.month,
					    'amount': payment.amount,
					    'employee_id': payment.employee_id.id,
					    'loan_type_id': payment.loan_id.loan_id.id,
					    'loan_id': payment.loan_id.id,
					    'payment_type':'direct_payment'})
					new_arc_id.action_done()  

					payment.create_move(payment.amount)
					
		self.write({'state':'paid'})

	def create_move(self,amount):
		for payment in self:
			move_id = self.env['account.move'].create({
				'move_type': 'entry',
				'invoice_date': payment.date,
				'journal_id':payment.journal_id.id,
				'partner_id':payment.loan_id.employee_id.address_home_id.id,
				'line_ids': [
					(0, None, {
						'name': (_('Loan Direct Payment For %s :-', payment.loan_id.name)),
						'debit': 0.0,
						'credit':  amount or 0.0,
						'quantity': 1.0,
						'date_maturity': payment.date,
						'currency_id': payment.loan_id.company_id.currency_id.id,
						'account_id': payment.loan_id.loan_id.loan_account_id.id,
						'partner_id': payment.loan_id.employee_id.address_home_id.id,
						'exclude_from_invoice_tab': False,
					}),
					(0, None, {
						'name': (_('Loan Direct Payment For %s :-', payment.loan_id.name)),
						'debit':amount or 0.0,
						'credit':0.0,
						'quantity': 1.0,
						'date_maturity': payment.date,
						'currency_id': payment.loan_id.company_id.currency_id.id,
						'account_id': payment.journal_id.payment_debit_account_id.id,
						'partner_id': payment.loan_id.employee_id.address_home_id.id,
						'exclude_from_invoice_tab': False
					,})
					]

				})
			move_id.post()
			payment.loan_id.write({'direct_payment_ids':[(4, move_id.id)]}) 


