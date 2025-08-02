# -*- coding: utf-8 -*-
from odoo import models, fields, api , _
from datetime import datetime, timedelta
from odoo.tools.float_utils import float_compare, float_is_zero, float_round


class product_template(models.Model):
	_inherit = "product.template"


	warranty = fields.Float(string="Warranty Period (Years)", )
	installation_required = fields.Boolean(string='Installation Required',)
	installation_instructions = fields.Html(string='Installation Instructions',)
	equipment_category_id = fields.Many2one(
		string="Equipment Category",
		comodel_name="maintenance.equipment.category",
	)
	installation_required = fields.Boolean(string='Installation Required',)
	installation_instructions = fields.Html(string='Installation Instructions',)
	installation_lead_time = fields.Float(string="Installation Lead Time (Days)", )
	maintenance_duration = fields.Float(string="Maintenance Duration (Hours)", )


class product_product(models.Model):
	_inherit = "product.product"


	warranty = fields.Float(string="Warranty Period (Years)",
	related='product_tmpl_id.warranty',
	readonly=True,
	store=True
	)
	installation_required = fields.Boolean(string='Installation Required',
	related='product_tmpl_id.installation_required',
	readonly=True,
	store=True
	)
	installation_instructions = fields.Html(string='Installation Instructions',
	related='product_tmpl_id.installation_instructions',
	readonly=True,
	store=True
	)
	equipment_category_id = fields.Many2one(
		string="Equipment Category",
		comodel_name="maintenance.equipment.category",
		related='product_tmpl_id.equipment_category_id',
		readonly=True,
		store=True
		
	)
	installation_required = fields.Boolean(string='Installation Required',
	related='product_tmpl_id.installation_required',
	readonly=True,
	store=True
	)
	installation_instructions = fields.Html(string='Installation Instructions',
	related='product_tmpl_id.installation_instructions',
	readonly=True,
	store=True
	)
	installation_lead_time = fields.Float(string="Installation Lead Time (Days)",
	related='product_tmpl_id.installation_lead_time',
	readonly=True,
	store=True
	)
	maintenance_duration = fields.Float(string="Maintenance Duration (Hours)",
	related='product_tmpl_id.maintenance_duration',
	readonly=True,
	store=True
	)	