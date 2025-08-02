# -*- encoding: utf-8 -*-
# © 2017 Mackilem Van der Laan, Trustcode
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models , _
from odoo.exceptions import ValidationError, UserError
from odoo.exceptions import Warning, ValidationError

class equipment_installation(models.Model):
	_name = 'equipment.installation'
	_inherit = ['mail.thread', 'mail.activity.mixin']
	_description = 'Equipment Installation'

	def _get_default_team_id(self):
		MT = self.env['maintenance.team']
		team = MT.search([('company_id', '=', self.env.user.company_id.id)], limit=1)
		if not team:
			team = MT.search([], limit=1)
		return team.id
	
	@api.depends('date_start', 'date_end')
	def _compute_actual_duration(self):
		for rec in self:
			rec.actual_duration = 0
			if rec.date_start and rec.date_end:
				start = fields.Datetime.from_string(rec.date_start)
				end = fields.Datetime.from_string(rec.date_end)
				delta = end - start
				rec.actual_duration = delta.total_seconds() / 3600

	name = fields.Char(string="Sequence", readonly=True , default="New")
	equipment_id = fields.Many2one(
		string="Equipment",
		comodel_name="maintenance.equipment",
		required=True,
	)
	category_id = fields.Many2one('maintenance.equipment.category', related='equipment_id.category_id', string='Category', store=True, readonly=True)
	customer_id = fields.Many2one(
		string="Customer",
		comodel_name="res.partner",
		# domain="[('customer', '=', True)]",
		required=True,
	)
	location = fields.Char('Location')
	instrustions = fields.Html(string="Installation Instructions", )
	assign_date = fields.Date('Assigned Date', tracking=True)
	model = fields.Char(string='Model',readonly=True,related="equipment_id.model")
	serial_id = fields.Many2one('stock.production.lot',string='Serial Number', copy=False , readonly=True,related="equipment_id.serial_id")
	request_date = fields.Date('Request Date', tracking=True, default=fields.Date.context_today,
							   help="Date requested for the installation to happen")
	priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority')
	color = fields.Integer('Color Index')
	active = fields.Boolean(default=True, help="Set archive to true to hide the Installation request without deleting it.")
	maintenance_team_id = fields.Many2one('maintenance.team', string='Team', default=_get_default_team_id)
	state = fields.Selection(
		string="State",
		selection=[
			('draft', 'Draft'),
			('assinged', 'Assigend'),
			('inprogress', 'In Progress'),
			('done', 'Done'),
			('cancel','Cancel'),
		],default="draft",
		tracking=True,
	)
	date_start = fields.Datetime(string='Actual Start')
	date_end = fields.Datetime(string='Actual End')
	actual_duration = fields.Float(string='Actual duration',
		compute=_compute_actual_duration,help='Actual duration in hours')
	job_ids = fields.One2many(
		string="Serviecs",
		comodel_name="job.line",
		inverse_name="installation_id",
	)
	invoice_id = fields.Many2one(
		string="Invoice",
		comodel_name="account.invoice",
		readonly=True,
	)
	trianig = fields.Selection(
		string="Trainning",
		selection=[
				('yes', 'With Trainning'),
				('no', 'Without Trainning'),
		],
	)

	def create_invoice(self):
		if self.invoice_id:
			raise Warning(_("Sorry !! this installation request is almost invoiced"))
		if not self.job_ids :
			raise Warning(_("Sorry !! there is no service to invoice"))
		
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
		})

	@api.model
	def create(self, values):
		if not values.get('name', False) or values['name'] == _('New'):
			values['name'] = self.env['ir.sequence'].next_by_code('equipment.installation') or _('New')
		return super(equipment_installation, self).create(values)
	
	def confirm(self):
		self.state = 'assinged'
	
	def start(self):
		self.state = 'inprogress'

	def complete(self):
		self.state = 'done'
	
	def cancel(self):
		self.state = 'cancel'
	
	def rest_to_draft(self):
		self.state = 'draft'