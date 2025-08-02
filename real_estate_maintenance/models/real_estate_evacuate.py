

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta

class RealEstateEvacuate(models.Model):

    _name = 'real.estate.evacuate'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Real Estate Evacuate'


    name = fields.Char(string="Name" , default=lambda self: _('New'), readonly=True)
    partner_id=fields.Many2one("res.partner", string="Owner" , required=True, domain=[('partner_type','=','owner')], context="{'default_partner_type': 'owner'}", ondelete="cascade", tracking=True)
    num_id = fields.Char(string="ID Number", related="partner_id.id_partner_number", tracking=True)
    phone = fields.Char(string="Phone Number", related="partner_id.phone", tracking=True)

    real_estate_id = fields.Many2one('real.estate', 'Real Estate', help='Real Estate', related='unit_id.base_property_id', tracking=True)
    unit_id = fields.Many2one('real.estate.units', string="Unit", required=True, related='contract_id.unit_id', tracking=True)
    property_floors = fields.Many2one('floors.model', related='unit_id.property_floors', tracking=True)

    evacuate_type = fields.Selection(selection=[('with_c', 'With contract'),
                                    ('without_c', 'Without contract')],
                                    required=True, tracking=True, default='with_c')


    contract_id = fields.Many2one('realestate.contract.model', states={'draft': [('readonly', False)]}, tracking=True)
    date = fields.Date(string=' Date ', related='contract_id.date', tracking=True)
    notify_date = fields.Date(string='Notify Date', related='contract_id.notify_date')
    date_start = fields.Date(string='Start Date ', related='contract_id.date_start')
    date_end = fields.Date(string='End Date', related='contract_id.date_end')
    evacuation_date = fields.Date(string='Evacuation Date', related='contract_id.evacuation_date')
    delivery_date = fields.Date(string='Delivery Date', related='contract_id.delivery_date')
    notify_d = fields.Date(string='Actual Notify Date', tracking=True)
    contract_period = fields.Float(string='Contract Duration (months)', compute="calculate_contract_period")


    number_id = fields.Char(string="Number", required=True, tracking=True)
    unit_num = fields.Char(string="Unit Number", required=True, tracking=True)
    date_con = fields.Date(string=' Date ', required=True, tracking=True)
    product_id = fields.Many2one('product.template', string="Related Product", tracking=True)
    invoice_id = fields.Many2one('account.move')

    total_amount = fields.Monetary(string='Total Amount', related='unit_id.unit_amount', tracking=True)
    month_amount = fields.Monetary(string='Month Amount', related='contract_id.month_amount',
     readonly=True, tracking=True)
    paid_amount = fields.Monetary(string='Paid Amount',compute='calculate_contract_payments', readonly=True, tracking=True)
    residual_amount = fields.Monetary(string='Residual Amount', compute='calculate_contract_payments', tracking=True)
    compensation_amount = fields.Monetary(string='Customer Compensation Amount', compute='calculate_compensation_amount', )
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency")

    state = fields.Selection([('draft', 'Draft'),
                              ('finance', 'Financial approval'),
                              ('investment', 'Investment approval'),
                              ('evacuate', 'Evacuate approval'),
                              ('general', 'General approval'),
                              ('approved', 'Approved'),],
                             'State', readonly=True, default='draft', tracking=True)

    @api.depends('date_start', 'date_end')
    def calculate_contract_period(self):
        for rec in self:
            if rec.date_start and rec.date_end:
                delta = relativedelta(rec.date_end, rec.date_start)
                rec.contract_period = delta.years * 12 + delta.months
            else:
                rec.contract_period = 0

    @api.depends('date_end', 'notify_d', 'month_amount')
    def calculate_compensation_amount(self):
        for rec in self:
            if rec.date_end and rec.notify_d and rec.month_amount:
                end_date = fields.Date.from_string(rec.date_end)
                notify_date = fields.Date.from_string(rec.notify_d)
                
                if notify_date > end_date:
                    # Calculate the difference in months
                    delta = relativedelta(notify_date, end_date)
                    months_difference = delta.years * 12 + delta.months + (delta.days / 30.0)
                    
                    # Calculate the compensation amount
                    rec.compensation_amount = abs(months_difference * rec.month_amount)
                else:
                    rec.compensation_amount = 0
            else:
                rec.compensation_amount = 0


    def calculate_contract_payments(self):
        for rec in self:
            if rec.contract_id.contract_amount != sum(line.paid_amount for line in rec.contract_id.payment_ids):
                rec.paid_amount = sum(line.pay_amount for line in rec.contract_id.payment_ids)
                rec.residual_amount = sum(line.paid_amount for line in rec.contract_id.payment_ids)
            else:
                rec.paid_amount =0
                rec.residual_amount =0


    def create_product(self):
        """Method to create related product of the unit."""
        for rec in self:
            if not rec.product_id:
                product = self.env['product.template'].create({
                    'name': rec.unit_id.unit_name,
                    'list_price': rec.unit_id.unit_amount,
                    'type': 'product',
                    'unit_id':rec.unit_id.id,
                    'investment_ok':True,
                    'sale_ok':True,
                    'purchase_ok':False,
                    'type':'consu'
                })
                rec.product_id = product.id

    def create_invoice(self):
        """Method to create the related invoice of the unit"""
        if not self.product_id:
            raise UserError("Please create the related product of the unit")
        for rec in self:
            invoice = self.env['account.move'].create({
                'partner_id':rec.partner_id.id,
                'invoice_date': fields.Date.today(),
                'move_type':'out_invoice',
                'invoice_line_ids':
                [(0, None, {
                            'name': 'Unit Sale' +  rec.unit_id.unit_name or '',
                            'product_id':  rec.product_id.id,
                            'price_unit':  rec.unit_id.unit_amount,
                            'quantity': 1.0,
                            'account_id': rec.product_id.property_account_income_id.id,
                        }),
                ]
                })
        self.invoice_id = invoice.id

    def open_invoice(self):
        domain = [ ('id', '=',self.invoice_id.id)]
        res_id = self.invoice_id.id  or False     
        return {
          'name': _('Sales'),           
          'domain': domain,          
          'res_model': 'account.move', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form,kanban',
          'help': _('''<p class="oe_view_nocontent_create">
           
                                    Attach
    documents of your employee.</p>'''),
         'limit': 80}

    @api.model
    def create(self, vals):
        code = 'real.estate.evacuate.code'
        if vals.get('name', 'New') == 'New':
            message = 'REV' + self.env['ir.sequence'].next_by_code(code)
            vals['name'] = message
        return super(RealEstateEvacuate, self).create(vals)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update the domain of contract_id based on the selected partner.

        """
        domain = [('partner_id', '=', self.partner_id.id)]
        domain += [('unit_id.state', '=', 'sold')]
        return {'domain': {'contract_id': domain}}

    def action_wait_finance(self):
        return self.write({'state': 'finance'})

    def action_wait_investment(self):
        return self.write({'state': 'investment'})

    def action_wait_evacuate(self):
        return self.write({'state': 'evacuate'})

    def action_wait_general(self):
        return self.write({'state': 'general'})

    def action_approve(self):
            self.write({'state': 'approved'})
            self.unit_id.write({'state':'evacuate'})


    
    