# Copyright (C) 2018 Open Source Integrators
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from datetime import datetime, timedelta
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import Warning, ValidationError


class maintenance_request(models.Model):
	_inherit = 'maintenance.request'

	@api.depends('date_start', 'date_end')
	def _compute_actual_duration(self):
		for rec in self:
			rec.actual_duration = 0
			if rec.date_start and rec.date_end:
				start = fields.Datetime.from_string(rec.date_start)
				end = fields.Datetime.from_string(rec.date_end)
				delta = end - start
				rec.actual_duration = delta.total_seconds() / 3600

	@api.onchange('duration')
	def onchange_scheduled_duration(self):
		if (self.duration and self.schedule_date):
			date_to_with_delta = fields.Datetime.from_string(
				self.schedule_date) + \
				timedelta(hours=self.duration)
			self.schedule_date_end = str(date_to_with_delta)

	schedule_date_end = fields.Datetime(string="Scheduled End")
	date_start = fields.Datetime(string='Actual Start')
	date_end = fields.Datetime(string='Actual End')
	actual_duration = fields.Float(string='Actual duration',
		compute=_compute_actual_duration,help='Actual duration in hours')
	todo = fields.Html(string="Instructions", )
	customer_id = fields.Many2one(
		string="Customer",
		comodel_name="res.partner",
	)
	'''
	parts_ids = fields.One2many('task.line', 'fleet_service_id', string='Parts')

	warehouse_id = fields.Many2one('stock.location', string='Warehouse')
	delivery_id = fields.Many2one('stock.picking', string='Delivery Reference', readonly=True)
	out_going_id = fields.Many2one('stock.picking', string='Out Going', readonly=True)

	invoice_id = fields.Many2one(
		string="Invoice",
		comodel_name="account.invoice",
		readonly=True,
	)
	job_ids = fields.One2many(
		string="service",
		comodel_name="job.line",
		inverse_name="maintenance_id",
	)
	invoiced = fields.Boolean(string="Invoiced?",readonly=True )

	def create_invoice(self):
		repaired_stage_id = self.env['maintenance.stage'].search([('repaired_stage','=',True)],limit=1)
		if not repaired_stage_id:
			raise Warning(_("Sorry !! Can you please specifiy repaired stage ?!"))
		if self.stage_id.repaired_stage:
			raise Warning(_("Sorry !! this installation is almost repaired and close"))
		if self.invoice_id:
			raise Warning(_("Sorry !! this installation request is almost invoiced"))
		if not self.job_ids and not self.parts_ids:
			raise Warning(_("Sorry !! there is no spare part or service to invoice"))
		
		journal_id = self.env.user.company_id.after_sale_journal_id
		if not journal_id:
			raise Warning(_("Sorry !! can you please configuer After sales journal "))
		invoice_id = self.env['account.invoice'].create({
			'partner_id':self.customer_id.id,
			'date_invoice':fields.Date.today(),
			'type':'out_invoice', 
			'journal_id': journal_id.id,
		})
		invoice_line_obj = self.env['account.invoice.line']
		for line in self.parts_ids:
			rslt = line.product_id.partner_ref if line.product_id.partner_ref else ""
			if line.product_id.description_purchase:
				rslt += '\n' + line.product_id.description_purchase
			if line.product_id.description_sale:
				rslt += '\n' + line.product_id.description_sale
			account_id = line.product_id.property_account_income_id or line.product_id.categ_id.property_account_income_categ_id
			if not account_id : 
				raise Warning(_("Please Make suer you configuerd income account for product or product category !!"))
			invoice_line_obj.create({
				'product_id':line.product_id.id,
				'price_unit':line.price_unit,
				'quantity':line.qty,
				'invoice_id':invoice_id.id,
				'name':rslt,
				'account_id':account_id.id,
			})
		for job_id in self.job_ids:
			account_id = job_id.product_id.property_account_income_id or job_id.product_id.categ_id.property_account_income_categ_id
			if not account_id : 
				raise Warning(_("Please Make suer you configuerd income account for product or product category !!"))
			invoice_line_obj.create({
				'product_id':job_id.product_id.id,
				'price_unit':job_id.price_unit,
				'name':job_id.name,
				'quantity':1.0,
				'invoice_id':invoice_id.id,
				'account_id':account_id.id,
			})
		self.write({
			'invoice_id' : invoice_id.id,
			'stage_id' : repaired_stage_id.id,
			'invoiced': True,
		})

	
	def close_reopened_wo(self):
		"""
		This method is used to update the existing shipment moves
		if WO parts are updated in terms of quantities or complete parts.
		"""
		stock_move_obj = self.env['stock.move']
		out_pick_type = self.env['stock.picking.type'].search([('sequence_code', '=', 'OUT'),('default_location_src_id','=',self.warehouse_id.id)], limit=1)
		if not out_pick_type or not out_pick_type[0].default_location_dest_id:
			raise Warning(_("Select Location has no default desitnation location ,, please select it first"))
		for work_order in self:
			ship_id = work_order.out_going_id 
			if ship_id:
				# If existing parts Updated
				move_ids = stock_move_obj.search([('picking_id', '=', ship_id.id)])
				if move_ids:
					self.remove_created_stock_moves(move_ids)
			else :
				ship_id = self.env['stock.picking'].create({
					'picking_type_id':out_pick_type.id,
					'location_id': self.warehouse_id.id,
					'location_dest_id': out_pick_type and out_pick_type[0].default_location_dest_id.id or False
				})

			for product in work_order.parts_ids:
				stock_vals = {
					'product_id': product.product_id and product.product_id.id or False,
					'name': product.product_id and product.product_id.name or '',
					'product_uom_qty': product.qty or 0.0,
					'product_uom': product.product_uom and product.product_uom.id or False,
					'location_id': out_pick_type.warehouse_id and out_pick_type.warehouse_id.lot_stock_id and out_pick_type.warehouse_id.lot_stock_id.id or False,                    
					'location_dest_id': out_pick_type and out_pick_type[0].default_location_dest_id.id or False ,
					'price_unit': product.price_unit,
					'picking_id': ship_id and ship_id.id,
					'picking_type_id': out_pick_type and out_pick_type.ids[0] or False
				}
				stock_move_obj.create(stock_vals)

			ship_id.action_confirm()
			ship_id.action_assign()
			ship_id.button_validate()

			work_order.out_going_id = ship_id.id

    '''
