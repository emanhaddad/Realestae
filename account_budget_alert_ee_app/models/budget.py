# -*- coding: utf-8 -*-

from odoo import fields, models, api, _
from odoo.exceptions import ValidationError

class BudgetLine(models.Model):
	_inherit = 'account.report.budget.item'


	allow2_manager = fields.Boolean("Allow to Maanger")
	warning_type = fields.Selection([('ignore', 'Ignore'),('warning','Warning'),('restrict','Restriction')])
	is_active = fields.Boolean("Active")

	def _compute_practical_amount(self):
		for line in self:
			acc_ids = line.general_budget_id.account_ids.ids
			date_to = line.date_to
			date_from = line.date_from
			if line.analytic_account_id.id:
				analytic_line_obj = self.env['account.analytic.line']
				domain = [('account_id', '=', line.analytic_account_id.id),
						  ('date', '>=', date_from),
						  ('date', '<=', date_to),
						  ]
				if acc_ids:
					domain += [('general_account_id', 'in', acc_ids)]

				where_query = analytic_line_obj._where_calc(domain)
				analytic_line_obj._apply_ir_rules(where_query, 'read')
				from_clause, where_clause, where_clause_params = where_query.get_sql()
				select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

			else:
				aml_obj = self.env['account.move.line']
				domain = [('account_id', 'in',
						   line.general_budget_id.account_ids.ids),
						  ('date', '>=', date_from),
						  ('date', '<=', date_to),
						  ('move_id.state', '=', 'posted')
						  ]
				where_query = aml_obj._where_calc(domain)
				aml_obj._apply_ir_rules(where_query, 'read')
				from_clause, where_clause, where_clause_params = where_query.get_sql()
				select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

			self.env.cr.execute(select, where_clause_params)
			line.practical_amount = self.env.cr.fetchone()[0] or 0.0


class BudgetLine(models.Model):
	_inherit = 'budget.line'


	allow2_manager = fields.Boolean("Allow to Maanger")
	warning_type = fields.Selection([('ignore', 'Ignore'),('warning','Warning'),('restrict','Restriction')])
	is_active = fields.Boolean("Active")

	def _compute_practical_amount(self):
		for line in self:
			acc_ids = line.general_budget_id.account_ids.ids
			date_to = line.date_to
			date_from = line.date_from
			if line.analytic_account_id.id:
				analytic_line_obj = self.env['account.analytic.line']
				domain = [('account_id', '=', line.analytic_account_id.id),
						  ('date', '>=', date_from),
						  ('date', '<=', date_to),
						  ]
				if acc_ids:
					domain += [('general_account_id', 'in', acc_ids)]

				where_query = analytic_line_obj._where_calc(domain)
				analytic_line_obj._apply_ir_rules(where_query, 'read')
				from_clause, where_clause, where_clause_params = where_query.get_sql()
				select = "SELECT SUM(amount) from " + from_clause + " where " + where_clause

			else:
				aml_obj = self.env['account.move.line']
				domain = [('account_id', 'in',
						   line.general_budget_id.account_ids.ids),
						  ('date', '>=', date_from),
						  ('date', '<=', date_to),
						  ('move_id.state', '=', 'posted')
						  ]
				where_query = aml_obj._where_calc(domain)
				aml_obj._apply_ir_rules(where_query, 'read')
				from_clause, where_clause, where_clause_params = where_query.get_sql()
				select = "SELECT sum(credit)-sum(debit) from " + from_clause + " where " + where_clause

			self.env.cr.execute(select, where_clause_params)
			line.practical_amount = self.env.cr.fetchone()[0] or 0.0


class PurchaseOrder(models.Model):
	_inherit = 'purchase.order'

	exceed_note = fields.Char("Warning Info", default="")
	is_warning  = fields.Boolean()

	def button_confirm(self):
		for record in self:
			today = record.date_order
			budget_ids = self.env['crossovered.budget'].search([
				('state','not in',['draft','cancel','done']),
				('date_from','<=',today),
				('date_to','>=',today)])
			if budget_ids:
				for budget in budget_ids:
					pname = []
					ppname = []
					flag = False 
					flag_w = False
					for bline in budget.crossovered_budget_line.filtered(lambda bline: bline.is_active == True):
						if self.order_line:						
							for pline in self.order_line:
								if bline.warning_type == 'warning' and bline.analytic_account_id == pline.account_analytic_id and pline.price_subtotal >= (abs(bline.planned_amount) - abs(bline.practical_amount)):
									if  pline.product_id.name not in pname:
										pname.append(pline.product_id.name)
									self.is_warning = True
									flag_w = True

								if bline.warning_type == 'restrict' and bline.analytic_account_id == pline.account_analytic_id and pline.price_subtotal >= (abs(bline.planned_amount) - abs(bline.practical_amount)) and not bline.allow2_manager:
									if pline.product_id.name not in ppname:
										ppname.append(pline.product_id.name)
									flag = True

								if bline.warning_type == 'restrict' and bline.allow2_manager and self.env.user.has_group('account.group_account_manager'):
									self.is_warning = True
									self.exceed_note = "Order amount exceeed than budget amount, but allow manager can also confirm order"

								if bline.warning_type == 'ignore':
									self.is_warning = True
									self.exceed_note = "Successfully confirmed Purchse order then proceed"
					if flag:
						raise ValidationError(_("Restriction on Confirm Purchase Order : Budget Limit exceeding on %s Product")% str(ppname))
					if flag_w:
						self.exceed_note = "Budget Limit exceeding on "+str(pname)+" products."
		res = super(PurchaseOrder,self).button_confirm()
		return res


class AccountMove(models.Model):
	_inherit = 'account.move'

	exceed_note = fields.Char("Warning Info", default="")
	is_warning  = fields.Boolean()


	def action_post(self):
		for record in self:
			today = record.invoice_date
			budget_ids = self.env['crossovered.budget'].search([
				('state','not in',['draft','cancel','done']),
				('date_from','<=',today),
				('date_to','>=',today)])
			if budget_ids:
				for budget in budget_ids:
					acc_name = []
					acc_name_res = []
					flag = False 
					flag_w = False
					for bline in budget.crossovered_budget_line.filtered(lambda bline: bline.is_active == True):
						if self.invoice_line_ids:
							for iline in self.invoice_line_ids:
								if bline.warning_type == 'warning' and bline.analytic_account_id == iline.analytic_account_id and iline.price_subtotal >= (abs(bline.planned_amount) - abs(bline.practical_amount)):
									if iline.account_id.name not in acc_name:
										acc_name.append(iline.account_id.name)
									self.is_warning = True
									flag_w = True
								if bline.warning_type == 'restrict' and bline.analytic_account_id == iline.analytic_account_id and iline.price_subtotal >= (abs(bline.planned_amount) - abs(bline.practical_amount)) and not bline.allow2_manager:
									if iline.account_id.name not in acc_name_res:
										acc_name_res.append(iline.account_id.name)
									flag = True
								
								if bline.warning_type == 'restrict' and bline.allow2_manager:
									self.is_warning = True
									self.exceed_note = "Budget limit exceed, but allow manager can validate Vendor Bill"
								
								if bline.warning_type == 'ignore':
									self.is_warning = True
									self.exceed_note = "Successfully confirmed Vendor Bills then proceed"
					if flag:
						raise ValidationError(_("Restriction on Validate Bill : Budget Limit exceeding on %s Account")% str(acc_name_res))
					if flag_w and self.is_warning:
						self.exceed_note = "Budget Limit exceeding for "+str(acc_name)+" Account."

		res = super(AccountMove,self).action_post()
		return res


