

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError


class RealEstateCustomerStatus(models.Model):

    _name = 'real.estate.customer.status'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'real Estate Customer Status'

    name = fields.Char(string="Name" , default=lambda self: _('New'))
    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        related='unit_id.base_property_id',)
    unit_id = fields.Many2one('real.estate.units', string="Unit", required=True, tracking=True)
    property_type = fields.Selection(
        'real.estate',
        tracking=True,
        related='unit_id.property_type')
    unit_state = fields.Selection(
        'real.estate',
        tracking=True,
        related='unit_id.state')
    booking_date = fields.Date(string='Booking date', tracking=True)
    amount_booking = fields.Monetary(tracking=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",  default=lambda self: self.env.company.currency_id.id)
    payment_method = fields.Selection([('cash','Cash'),('bank','Bank')], string='Payment method', tracking=True)
    sales_user_id = fields.Many2one("res.users", string="Sales person", tracking=True)


    partner_id = fields.Many2one("res.partner", string="Customer" ,  ondelete="cascade", required=True, tracking=True)
    housing_support = fields.Selection([('h_yes','Deserves'),('h_no','Not Deserves')],string='Housing Support', tracking=True)
    housing_attachment =fields.Binary(string='Housing support attachment', tracking=True)

    finance_support = fields.Selection([('f_yes','Supported'),('f_no','Not Supported')], string='Finance Support', tracking=True)
    finance_attachment =fields.Binary(string='Finance support attachment', tracking=True)

    bank_statement = fields.Char(tracking=True)
    bank_attachment =fields.Binary(string='Bank statement attachment', tracking=True)
    evaluation_amount = fields.Monetary(tracking=True)



    funding_contract = fields.Selection([('c_yes','Complete'),('c_no','Not Complete')], string='Funding contract state', tracking=True)
    funding_attachment =fields.Binary(string='Funding contract attachment', tracking=True)

    evacuation_state = fields.Selection([('e_yes','Evacuation'),('e_no','Not Evacuation')], string='Evacuation status', tracking=True)
    evacuation_attachment =fields.Binary(string='Evacuation attachment', tracking=True)
    evacuation_date = fields.Date(string='Evacuation date', tracking=True)

    check_state = fields.Selection([('s_yes','Issued'),('s_no','Not Issued')], string='Issuing a check', tracking=True)

    
    taxes = fields.Selection([('t_yes','Paid'),('t_no','Not Paid')], string='Real estate transaction', tracking=True)
    taxes_amount = fields.Float(tracking=True)

    state = fields.Selection([('new', 'New'),
                              ('wait', 'Waiting to complete documents'),
                              ('confirmed', 'Confirmed'),
                              ('cancel', 'Cancelled'),],
                             'State', readonly=True, default='new', tracking=True)

    
    @api.model
    def create(self, vals):
        # if vals.get('name', _('New')) == _('New'):
        #     vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.booking') or _('New')

        result = super(RealEstateCustomerStatus, self).create(vals)
        return result

    def action_wait(self):
        return self.write({'state': 'wait'})

    def action_confirm(self):
        return self.write({'state': 'confirmed'})


    def action_cancel(self):
        return self.write({'state': 'cancel'})


    def action_booked(self):
        self.write({'state': 'wait'})
        # self.unit_id.write({'state': 'booked'})
        


    
    