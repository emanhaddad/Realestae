

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError


class RealEstateBooking(models.Model):

    _name = 'real.estate.booking'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'real Estate booking'

    name = fields.Char(string="Name" , default=lambda self: _('New'))
    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        related='unit_id.base_property_id',
        tracking=True,
        store=True,)
    unit_id = fields.Many2one(
        'real.estate.units', 
        string="Unit", 
        domain=[('state','=','available')],
        required=True, 
        tracking=True)
    property_type = fields.Selection(
        'real.estate',
        related='unit_id.property_type',
        tracking=True)
    unit_state = fields.Selection(
        'real.estate',
        related='unit_id.state',
        tracking=True)
    unit_space = fields.Float(
        'real.estate',
        related='unit_id.unit_space',
        tracking=True)
    currency_id = fields.Many2one(
        'res.currency', 
        help='The currency used to enter statement', 
        string="Currency", 
        oldname='currency')
    unit_amount= fields.Monetary( 
        string="Unit Price",
        related='unit_id.unit_amount',
        tracking=True)
    property_floors = fields.Many2one(
        'floors.model',
        related='unit_id.property_floors',
        tracking=True)
    state = fields.Selection([('new', 'New'),
                              ('wait', 'Waiting'),
                              ('confirmed', 'Confirmed'),
                              ('sale', 'Sales Contract'),
                              ('cancel', 'Cancelled'),
                              ('canceled', 'Payment Vouchers Created'),],
                             'State', readonly=True, default='new', tracking=True)
    partner_id=fields.Many2one("res.partner", string="Customer" , tracking=True, domain=[('partner_type','=','owner')],
     context="{'default_partner_type': 'owner'}", ondelete="cascade")
    id_partner_number = fields.Char(
        'res.partner',
        related='partner_id.id_partner_number', tracking=True)
    phone = fields.Char(
        'res.partner',
        related='partner_id.phone', tracking=True)
    sales_user_id=fields.Many2one("res.users", string="Sales person",default= lambda self: self.env.user.id,  ondelete="cascade")
    date = fields.Date(
        string=' Date',
        tracking=True
    )
    attachment_id =fields.Binary(string='payment attachment', tracking=True)
    cancel_reason_id =fields.Many2one('booking.cancel.reason', string='Cancellation reason', tracking=True)
    payment_ids =fields.Many2many('account.payment', string='Payments')
    customer_ids = fields.Many2many('real.estate.customer.status', string='Customer status', tracking=True)
    account_id = fields.Many2one('account.account', tracking=True,default= lambda self: self.env.user.company_id.account_id, groups="account.group_account_user")
    journal_id = fields.Many2one('account.journal', tracking=True, domain=[('type','in',('cash','bank'))], groups="account.group_account_user")
    cost_center = fields.Many2one('account.analytic.account', tracking=True,groups="account.group_account_user")
    amount = fields.Monetary(tracking=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",  default=lambda self: self.env.company.currency_id.id)
    booking_description = fields.Char(string='Description', tracking=True)
    payment_method = fields.Selection([('cash','Cash'),('bank','Bank')], tracking=True, string='Payment method', required=True)
    check_number = fields.Char(string="Bank Transfer /Check num", tracking=True)
    contract_id = fields.Many2one('realestate.contract.model', tracking=True)
    realestate_contract_ids = fields.Many2many('realestate.contract.model', tracking=True, string='RealEstate Sale Contract')
    payment_move_id = fields.Many2one('account.move',string='payment Ref',readonly=True, tracking=True)
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    check_deserve = fields.Boolean(string= 'Deserve?', tracking=True)

        
    def create_paymnet(self):
        if self.check_deserve:
            if self.state == 'canceled':
                raise UserError('The returning deposit has already been created you cannot create another, check the "Return Deposit" for more details')

            if not self.exchange_type_id:
                raise UserError('Please select the exchange type')
            
            payment_id = self.env['cash.order'].create({
                # 'state': 'general',
                # 'name': new_cash_order_name,
                'date': self.date,
                'exchange_type_id' : self.exchange_type_id.id,
                'partner_id': self.partner_id.id,
                'amount' : self.amount,
                'journal_id' : self.journal_id.id,
                'disc' : ('إلغاء عربون حجز الوحدة: '+ self.unit_id.unit_name),
                'booking_request_ids' : self.id,
                'order_line_ids': [(0, 0, {
                    'description': 'أمر صرف',
                    'account_id': self.account_id.id,
                    'amount': self.amount,
                    # 'state': 'general',
                })],
            })
            payment_id.action_confirm()
            payment_id.action_finance()
            self.payment_move_id = payment_id.move_id.id
            return self.write({'state': 'canceled'})
        else:
            return self.write({'state': 'cancel'})


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.booking') or _('New')
        unit = self.env['real.estate.units'].browse(vals.get('unit_id'))
        
        # Check if the unit is available
        if unit.state != 'available':
            raise UserError(_('You cannot create a booking for an unavailable unit'))
        
        # Change the unit state to 'booked'
        unit.state = 'booked'
        
        result = super(RealEstateBooking, self).create(vals)
        return result

    def set_to_new(self):
        self.write({'state':'new'})


    def action_wait(self):
        if not self.account_id or not self.journal_id:
            raise ValidationError(_('Please set account and journal for this booking'))
        
        payment_id = self.env['cash.receive'].create({
                    # 'state': 'general',
                    # 'name': new_cash_receive_name,
                    'date': self.date,
                    'partner_id': self.partner_id.id,
                    'amount': self.amount,
                    'journal_id' : self.journal_id.id,
                    'disc' : self.name + ' ' + 'عربون الحجز رقم' + '\n' + self.payment_method + ' ' + 'طريقة الدفع' ,
                    'booking_request_ids' : self.id,
                    'order_line_ids': [(0, 0, {
                        'description': 'سند عربون الحجز',
                        'account_id': self.account_id.id,
                        'amount': self.amount,
                        # 'state': 'general',
                    })],
                })

        payment_id.action_confirm()
        payment_id.action_finance()
        self.payment_move_id = payment_id.move_id.id
        return self.write({'state': 'confirmed'})

    def unlink(self):
        for record in self:
            if record.payment_move_id:
                raise ValidationError(_('You cannot delete a booking that has a payment move associated with it. Please archive it instead.'))
            if record.unit_id.state == 'booked':
                raise UserError('You cannot delete a deposit for a booked unit you need to cancel it instead')
        return super(RealEstateBooking, self).unlink()

    def open_move(self):
    
        tree_view = self.env.ref('cash_request.cash_receive_tree_view')
        form_view = self.env.ref('cash_request.cash_receive_view')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipt Vouchers',
            'res_model': 'cash.receive',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': {'default_name': self.display_name},
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('booking_request_ids', '=', self.id)],

        }

    def open_cancel_move(self):
    
        tree_view = self.env.ref('cash_request.cash_order_tree_view')
        form_view = self.env.ref('cash_request.cash_order_view')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Vouchers',
            'res_model': 'cash.order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'context': {'default_name': self.display_name},
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('booking_request_ids', '=', self.id)],

        }

    def action_sale(self):
        contract=False
        contract = self.env['realestate.contract.model'].create({'unit_id':self.unit_id.id,
            'partner_id':self.partner_id.id,
            'representative_id':self.env.user.partner_id.id,
            'contract_type':'specific_units',
            'contract_amount':self.unit_amount - self.amount,
            'date': fields.Date.today(),
            'property_id':self.unit_id.base_property_id.id,
            'contract_account_type':'payment',
            'contract_partner_type':'sale'
            })
        self.write({'state': 'sale'})
        self.contract_id = contract.id
        self.realestate_contract_ids = [(4,contract.id)]

    def open_csale(self):
        domain = [ ('id', 'in',self.realestate_contract_ids.ids)]
        return {
          'name': _('Status'),           
          'domain': domain,          
          'res_model': 'realestate.contract.model', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form',
          'help': _('''<p class="oe_view_nocontent_create">
           
                                    Attach
    documents of your sales.</p>'''),
         'limit': 80,
         }

    def action_cancel(self):
        return self.write({'state': 'cancel'})


    def action_booked(self):
        if not self.attachment_id :
            raise ValidationError(_('Please insert payment attach for this booking'))
        customer = self.env['real.estate.customer.status'].sudo().create({
            'name':'Booking Number ' + self.name,
            'partner_id':self.partner_id.id,
            'sales_user_id':self.sales_user_id.id,
            'payment_method':self.payment_method,
            'unit_id':self.unit_id.id,
            'booking_date':self.date,
            'amount_booking':self.amount,})
        self.customer_ids = [(4,customer.id)]
        self.write({'state': 'wait'})

    def open_customer(self):
        domain = [ ('id', 'in',self.customer_ids.ids)]
        return {
          'name': _('Status'),           
          'domain': domain,          
          'res_model': 'real.estate.customer.status', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form',
          'help': _('''<p class="oe_view_nocontent_create">
           
                                    Attach
    documents of your employee.</p>'''),
         'limit': 80,
         }
        


    
    