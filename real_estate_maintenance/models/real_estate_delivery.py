

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta


class RealEstateDelivery(models.Model):

    _name = 'real.estate.delivery'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'real Estate delivery'


    # def get_total_rental_fees(self):
    #     for rec in self:
    #         delta_days=(rec.real_notify_date - rec.contract_id.notify_date).days / 30.0
    #         if delta_days>0:
    #             rec.total_rental = rec.monthly_rental * delta_days
    #         else:
    #             rec.total_rental =0

    def get_total_amount(self):
        for rec in self:
            rec.total_amount = rec.amount 

    def calculate_contract_payments(self):
        for rec in self:
            if len(rec.contract_id.payment_ids.ids):
                rec.paid_amount = rec.contract_id.residual_amount
                rec.residual_amount = rec.contract_id.residual_amount
            else:
                rec.paid_amount =0
                rec.residual_amount =0

    name = fields.Char(string="Name" , default=lambda self: _('New'), readonly=True)
    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        related='unit_id.base_property_id',)
    unit_id = fields.Many2one('real.estate.units', tracking=True, string="Unit", required=True, related='contract_id.unit_id')
    state = fields.Selection([('new', 'New'),
                              ('wait_finance_approve', 'Waiting Financial approval'),
                              ('wait_investment_approve', 'Waiting investment approval'),
                              ('wait_ceo_approve', 'Waiting CEO approval'),
                              ('confirmed', 'Confirmed'),],
                             'State', readonly=True,default='new', tracking=True)

    
    partner_id=fields.Many2one("res.partner", string="Customer" , tracking=True, required=True,domain=[('partner_type','=','owner')], context="{'default_partner_type': 'owner'}", ondelete="cascade")
    num_id = fields.Char(string="ID Number", related="partner_id.id_partner_number", tracking=True)
    phone = fields.Char(string="Phone Number", related="partner_id.phone", tracking=True)
    contract_id = fields.Many2one('realestate.contract.model', required=True, tracking=True)
    evacuation_date = fields.Date(string=' Date Evacuation',readonly=True, tracking=True, related='contract_id.evacuation_date')
    delivery_date = fields.Date(string='Delivery Date', related='contract_id.delivery_date', tracking=True)
    notify_date = fields.Date(string='Notify Date',readonly=True, related='contract_id.notify_date', tracking=True)
    actual_delivere = fields.Date(string='Actual Deliver Day', required=True, tracking=True)

    # total_amount = fields.Monetary(string='Total Amount', compute='get_total_amount' )
    # amount = fields.Monetary(string=' Amount', related='contract_id.contract_amount',
    #  readonly=True)
    # paid_amount = fields.Monetary(string='Paid Amount',compute='calculate_contract_payments')
    # residual_amount = fields.Monetary(string='Residual Amount', compute='calculate_contract_payments')
    # monthly_rental= fields.Monetary(string='Monthly rental fees', related='contract_id.monthly_rental', 
    #     readonly=True)
    # currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency")
    
    # total_rental = fields.Monetary('Total rental fees', compute='get_total_rental_fees')
    narration = fields.Char('Narration')

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update the domain of contract_id based on the selected partner.

        """
        domain = [('partner_id', '=', self.partner_id.id)]
        domain += [('unit_id.state', '=', 'evacuate')]
        return {'domain': {'contract_id': domain}}

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.delivery') or _('New')

        result = super(RealEstateDelivery, self).create(vals)
        return result

    def set_to_new(self):
        self.write({'state':'new'})


    def action_wait_finance(self):
        return self.write({'state': 'wait_finance_approve'})

    def action_wait_investment(self):
        # self.env['rent.contract.payment'].create({'rental_fees':True,'pay_amount':self.amount,'renter_id':self.partner_id.id,'analytic_id': self.contract_id.id,
        #     #'property_id':self.property_id.id
        #     })
        return self.write({'state': 'wait_investment_approve'})

    def action_ceo_waiting(self):
        return self.write({'state': 'wait_ceo_approve'})

    '''
    def action_cancel(self):
        return self.write({'state': 'cancel'})
    '''
    @api.depends('actual_delivere')
    def action_confirm(self):
        if not self.real_estate_id.warranty_start_date:
            self.real_estate_id.write({'warranty_start_date':self.actual_delivere,'warranty_end_date':self.actual_delivere + relativedelta(years=1)})
        self.unit_id.write({'owner_id':self.partner_id.id,'state':'delivered'})
        self.write({'state': 'confirmed'})
        # move_line_1={
        #     'name': _("Income of %s", self.unit_id.unit_name),
        #     'account_id': self.env.user.company_id.account_id.id,
        #     'debit': abs(self.amount),
        #     'analytic_account_id':self.real_estate_id.analytic_id.id,
        #     'credit': 0,
        #     #'display_type':'line_note'
        # }
        # move_line_2={
        #         'name':_(""),
        #         'account_id':  self.partner_id.property_account_receivable_id.id,
        #         'debit':0,
        #         'credit':abs(self.amount)}

        # move_vals = {
        #     'journal_id': self.env.user.company_id.income_journal_id.id,
        #     'move_type': 'entry',
        #     'partner_id' :self.partner_id.id,
        #     'ref': _("delivery of  %s", self.unit_id.unit_name),
        #     'date': fields.Date.today(),
        #     'line_ids': [(0, 0,move_line_1)
        #     ,(0, 0,move_line_2)],
        #     }
        # account_move = self.env['account.move'].create(move_vals)


    
    