
# -*- coding: utf-8 -*-
from odoo import models, fields, api , _
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

class Picking(models.Model):
	_inherit = "stock.picking"

	def button_validate(self):
		if self.picking_type_id.code == 'outgoing':
			product_id = None
			equipment = self.env['maintenance.equipment']
			for line in self.move_ids_without_package:
				for move in line.move_line_ids:
					model_number = " "
					product_id = line.product_id.product_tmpl_id
					if product_id.is_machine :
						scrap_date = False
						warranty_date = False
						if product_id.equipment_life_span:
							scrap_date = datetime.now() + relativedelta(years=int(product_id.equipment_life_span))
						if product_id.warranty:
							warranty_date = datetime.now() + relativedelta(years=int(product_id.warranty))
						if product_id.model_number:
							model_number = product_id.model_number	
						equipment_id = equipment.create({
							'name': product_id.name + " / " + model_number ,
							'category_id':product_id.equipment_category_id.id,
							'equipment_assign_to':'customer',
							'customer_id':self.partner_id.id,
							'scrap_date':scrap_date,
							'assign_date':datetime.now(),
							'partner_id':product_id.variant_seller_ids and \
								product_id.variant_seller_ids[0].name.id,
							'model':product_id.model_number,
							'warranty_date':warranty_date,
							'cost':product_id.list_price,
							'period': product_id.preventive_maintenance and \
								(product_id.preventive_maintenance * 30.0),
							'serial_id':move.lot_id.id		
						})
						if product_id.installation_required :
							self.env['equipment.installation'].create({
								'equipment_id':equipment_id.id,
								'customer_id':self.partner_id.id,
								'instrustions':product_id.installation_instructions
							})

					



		return super(Picking, self).button_validate()
