

from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
import logging
_logger = logging.getLogger(__name__)

class RealEstateSales(models.Model):

    _name = 'real.estate.sale'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'real Estate sales'


    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            vals['name'] = self.env['ir.sequence'].next_by_code('real.estate.sale') or _('New')

        result = super(RealEstateSales, self).create(vals)
        return result

    name = fields.Char(string="Name" , default=lambda self: _('New'), readonly=True)
    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        related='unit_id.base_property_id', tracking=True)
    unit_id = fields.Many2one('real.estate.units', 
                            string="Unit", 
                            required=True, 
                            tracking=True)
    state = fields.Selection([('new', 'New'),
                              ('first_confirm', 'First confirm'),
                              ('confirmed', 'Confirmed'),
                              ('cancel', 'Cancelled'),],
                             'State', readonly=True,default='new', tracking=True)
    resale = fields.Boolean(string= 'Resale?', tracking=True)


    def calculate_contract_payments(self):
        for rec in self:
            rec.paid_amount = rec.contract_id.paid_amount
            rec.residual_amount = rec.contract_id.residual_amount
            
    @api.onchange('commission_lines')
    def calculate_commission(self):
        for rec in self:
            if len(rec.commission_lines.ids):
                rec.commission = sum(rec.commission_lines.mapped('amount'))
                # if rec.commission > rec.property_commission and rec.property_commission!=0:
                #     raise ValidationError(_('total of commission must not be more than %s' % rec.property_commission))
            else:
                rec.commission =0

    @api.onchange('unit_id')
    def get_commission_property(self):
        for rec in self:
            if rec.real_estate_id.commission_type == 'fixed':
                rec.property_commission= rec.real_estate_id.commission_amount
            if rec.unit_id.state=='booked':
                booking_rec = self.env['real.estate.booking'].search([('state','=','confirmed'),('unit_id','=',rec.unit_id.id)])
                if booking_rec:
                    rec.partner_id =  booking_rec.partner_id.id
            
    
    partner_id=fields.Many2one("res.partner", string="Customer" ,  ondelete="cascade", tracking=True)
    marketing_user_id=fields.Many2one("res.users", string="Marketing person",  ondelete="cascade", tracking=True)
    sales_user_id=fields.Many2one("res.users", string="Sales person",default= lambda self: self.env.user.id,  ondelete="cascade", tracking=True)
    date = fields.Date(string=' Date', index=True, tracking=True)
    customer_type= fields.Selection([('normal','Normal'),('investor','Investor')], tracking=True)
    property_type= fields.Selection([('ready','Ready'),('under_construction','Under construction'),('final_prepare','Final prepare')], related='unit_id.property_type', tracking=True)
    delivery_date = fields.Date(string='Delivery Date', tracking=True)
    evacuation_date = fields.Date(string='Evacuation Date', tracking=True)
    real_notify_date = fields.Date(string='Real notify Date', tracking=True)
    delivery_period = fields.Char('Delivery period', tracking=True)
    total_amount = fields.Monetary(string='Total Amount', tracking=True)
    commission = fields.Monetary(string='Total of Commissions',compute='calculate_commission', tracking=True, store=True)
    property_commission = fields.Monetary(tracking=True)
    amount = fields.Monetary(string=' Amount', related='unit_id.unit_amount', tracking=True, store=True)
    invoice_ids =fields.Many2many('account.move', string='Invoices', tracking=True)
    #payment_ids =fields.Many2many('account.payment', string='Payments', )
    payment_ids =fields.Many2many('rent.contract.payment', string='Payments', tracking=True)
    paid_amount = fields.Monetary(string='Paid Amount',compute='calculate_contract_payments', tracking=True)
    residual_amount = fields.Monetary(string='Residual Amount', compute='calculate_contract_payments')
    monthly_rental= fields.Monetary(string='Monthly rental fees', tracking=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",
         default=lambda self: self.env.company.currency_id.id)
    commission_lines= fields.One2many('real.estate.sale.commission','sale_id')
    contract_id = fields.Many2one('realestate.contract.model')
    sale_type = fields.Selection(selection=[('sale','Sale'),('resale','Resale')],
                                    required=True, tracking=True, default='sale')
    resale_type = fields.Selection(selection=[('with_d','Delegate'),('without_d','Without Delegate')], tracking=True, default='without_d')

    delegate_name = fields.Many2one('real.estate.delegate', domain=[('state','=','approved')])
    delegate_partner_id =fields.Many2one("res.partner", string="Owner" , tracking=True, related='delegate_name.partner_id')
    delegate_contract_id = fields.Many2one('realestate.contract.model', tracking=True, related='delegate_name.contract_id')
    marketing_amount = fields.Monetary(string='Marketing Amount', tracking=True, related='delegate_name.marketing_amount')
    owner_amount = fields.Monetary(string="Owner's Amount", tracking=True, related='delegate_name.owner_amount')
    total_amount = fields.Monetary(string='Total Amount', tracking=True, related='delegate_name.total_amount')

    move_id = fields.Many2one('account.move', string='Owner Move',readonly=True, tracking=True)
    buyer_move_id = fields.Many2one('account.move', string='Buyer Move',readonly=True, tracking=True)
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    journal_id = fields.Many2one('account.journal', tracking=True, domain="[('type', 'in', ('cash','bank'))]")
    account_id = fields.Many2one('account.account', tracking=True)
    analytic_account_id = fields.Many2one('account.analytic.account', tracking=True)
    resale_ids = fields.Many2one('real.estate.sale', string="Resale Request", readonly=True, copy=False, tracking=True)

    owner_id = fields.Many2one('res.partner', string='Owner', tracking=True, readonly=True, related='unit_id.owner_id')
    buyer_id = fields.Many2one('res.partner', string='Buyer/ New Customer', tracking=True)
    marketing_am = fields.Monetary(string='Marketing Amount', tracking=True)
    owner_am = fields.Monetary(string="Owner's Amount", tracking=True)
    total_am = fields.Monetary(string='Total Amount', tracking=True, compute='get_total')

    @api.depends('marketing_am', 'owner_am')
    def get_total(self):
        for rec in self:
            if rec.marketing_am and rec.owner_am:
                rec.total_am = rec.marketing_am + rec.owner_am
            else:
                rec.total_am =0



    @api.onchange('unit_id')
    def _onchange_unit_id(self):
        """Update the domain of delegate_name based on the selected unit_id.

        """
        domain = [('state', '=', 'approved')]
        if self.unit_id:
            domain.append(('unit_id', '=', self.unit_id.id))
        else:
            domain = []
        return {'domain': {'delegate_name': domain}}


    @api.onchange('sale_type', 'resale_type')
    def _onchange_sale_type(self):
        """Update the domain of unit_id based on the selected sale_type.

        """
        if self.sale_type == 'sale':
            domain = [('state', '=', 'available')]
        else:
            if self.resale_type == 'with_d':
                domain = [('state', '=', 'delegated')]
            else:
                domain = [('state', '=', 'sold')]
        return {'domain': {'unit_id': domain}}

    def action_payment(self):
    
        tree_view = self.env.ref('cash_request.cash_order_tree_view')
        form_view = self.env.ref('cash_request.cash_order_view')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Vouchers',
            'res_model': 'cash.order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('resale_ids', '=', self.id)],
        }
    
    
    def set_to_new(self):
        self.write({'state':'new'})


    @api.onchange('unit_id')
    def onchange_unit(self):
        for rec in self:
            if rec.unit_id.state=='booked':
                booking_recs=self.env['real.estate.booking'].search([('unit_id','=',rec.unit_id.id),('state','=','confirmed')])
                if booking_recs:
                    rec.partner_id = booking_recs.mapped('partner_id').ids[0]
                    return {'domain':{'partner_id':[('id','in',booking_recs.mapped('partner_id').ids)]} }




    def action_cancel(self):
        return self.write({'state': 'cancel'})


    def action_first_confirm(self):
        ''' Buyer Move
        '''
        if self.sale_type == 'resale':
            # Handle resale with delegation
            if self.resale_type == 'with_d':
                move_vals = {
                    'journal_id': self.journal_id.id,
                    'ref': self.unit_id.unit_name + " الوحدة " + self.name + ' إعادة بيع ',
                    'date': self.date or fields.Date.today(),
                    'line_ids': [
                        # Credit: from journal's default account
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.journal_id.default_account_id.id,
                            'partner_id': self.buyer_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': 0,
                            'credit': abs(self.owner_amount),
                        }),
                        # Debit: to selected account
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.account_id.id,
                            'partner_id': self.buyer_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': abs(self.owner_amount),
                            'credit': 0,
                        })
                    ]
                }

                account_move = self.env['account.move'].create(move_vals)
                self.write({'buyer_move_id': account_move.id})

            # Handle resale without delegation
            else:
                move_vals = {
                    'journal_id': self.journal_id.id,
                    'ref': self.unit_id.unit_name + " الوحدة " + self.name + ' إعادة بيع ',
                    'date': self.date or fields.Date.today(),
                    'line_ids': [
                        # Credit: from journal's default account
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.journal_id.default_account_id.id,
                            'partner_id': self.buyer_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': 0,
                            'credit': abs(self.owner_am),
                        }),
                        # Debit: to selected account
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.account_id.id,
                            'partner_id': self.buyer_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': abs(self.owner_am),
                            'credit': 0,
                        })
                    ]
                }

                account_move = self.env['account.move'].create(move_vals)
                self.write({'buyer_move_id': account_move.id})

            # Update the unit's buyer
            self.unit_id.write({'buyer_id': self.buyer_id.id})

        return self.write({'state': 'first_confirm'})


    def action_confirm(self):
        ''' Owner Move
        '''
        if self.sale_type == 'sale':
            owner_vals = {
                            'name': self.partner_id.name
                            # 'date': self.delivery_date
                        }
            self.real_estate_id.write({'owner_ids': [(0, 0, owner_vals)]})
            # self.real_estate_id.write({'owner_ids':[(4,self.partner_id.id)]})
        else:
            # Handle resale with delegation
            if self.resale_type == 'with_d':
                move_vals = {
                    'journal_id': self.journal_id.id,
                    'ref': self.unit_id.unit_name + " الوحدة " + self.name + ' إعادة بيع ',
                    'date': self.date or fields.Date.today(),
                    'line_ids': [
                        # Credit: from journal's default account
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.journal_id.default_account_id.id,
                            'partner_id': self.delegate_partner_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': abs(self.total_amount),
                            'credit': 0,
                        }),
                        # Debit: to selected account
                        (0, 0, {
                            'name': self.name + "عمولة اعادة البيع",
                            'account_id': self.account_id.id,
                            'partner_id': self.delegate_partner_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': 0,
                            'credit': abs(self.marketing_amount),
                        }),
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.account_id.id,
                            'partner_id': self.delegate_partner_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': 0,
                            'credit': abs(self.owner_amount),
                        })
                    ]
                }

                account_move = self.env['account.move'].create(move_vals)
                self.write({'move_id': account_move.id})

            # Handle resale without delegation
            else:
                move_vals = {
                    'journal_id': self.journal_id.id,
                    'ref': self.unit_id.unit_name + " الوحدة " + self.name + ' إعادة بيع ',
                    'date': self.date or fields.Date.today(),
                    'line_ids': [
                        # Credit: from journal's default account
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.journal_id.default_account_id.id,
                            'partner_id': self.owner_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': abs(self.total_am),
                            'credit': 0,
                        }),
                        # Debit: to selected account
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.account_id.id,
                            'partner_id': self.owner_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': 0,
                            'credit': abs(self.marketing_am),
                        }),
                        (0, 0, {
                            'name': self.name,
                            'account_id': self.account_id.id,
                            'partner_id': self.owner_id.id,
                            'analytic_account_id': self.analytic_account_id.id,
                            'debit': 0,
                            'credit': abs(self.owner_am),
                        })
                    ]
                }

                account_move = self.env['account.move'].create(move_vals)
                self.write({'move_id': account_move.id})
                self.move_id.post()
                self.buyer_move_id.post()            

            self.unit_id.write({'state': 're_sold'})

        return self.write({'state': 'confirmed'})


class RealEstateSale(models.Model):

    _name = 'real.estate.sale.commission'
    _description = 'Sale Commission'
    _rec_name='sale_id'

    sale_id = fields.Many2one(
        'real.estate.sale',
        'Sale ',
        )
    # commission_sale_id = fields.Many2one('realestate.contract.model', string='Sale Commission')
    partner_id = fields.Many2one(
        'res.partner',
        'partner',
        required=True,
        tracking=True
        )
    journal_id = fields.Many2one('account.journal', tracking=True)
    amount = fields.Monetary(string="Amount", required=True, default= lambda self: self.sale_id.real_estate_id.commission_amount, tracking=True, store=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",default=lambda self: self.env.company.currency_id.id, tracking=True)
    account_id = fields.Many2one('account.account', tracking=True)
    check = fields.Boolean("Payment Created?", readonly=True, tracking=True)
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    sale_commission_type = fields.Selection([
                            ('land', 'Land Commission'),
                            ('shares', 'Shares Commission'),
                            ('sale', 'Sale Commission'),],
                            'Sale Commission', readonly=True, default='sale', tracking=True)

    def set_button(self):
        for rec in self:
            rec.check = True

    def create_payment(self):
        if not self.journal_id:
            raise UserError('Please set the journal for this payment')
        if not self.account_id:
            raise UserError('Please set the account for this payment')
        if not self.exchange_type_id:
            raise UserError('Please set the exchange type for this payment')

        self.set_button()
        payment_id = self.env['cash.order'].create({
                    # 'state': 'general',
                    # 'name': new_cash_order_name,
                    'date': fields.date.today(),
                    'exchange_type_id' : self.exchange_type_id.id,
                    'partner_id': self.partner_id.id,
                    'amount' : self.amount,
                    'journal_id' : self.journal_id.id,
                    'disc' : self.sale_id.name + ' ' + 'عمولة عملية البيع رقم',
                    'commission_request_ids' : self.id,
                    'order_line_ids': [(0, 0, {
                        'description': 'أمر صرف لعموله',
                        'account_id': self.account_id.id,
                        'amount': self.amount,
                        # 'state': 'general',
                    })],
                })
        payment_id.action_confirm()
        payment_id.action_finance()

    # def action_payment(self):
    
    #     tree_view = self.env.ref('cash_request.cash_order_tree_view')
    #     form_view = self.env.ref('cash_request.cash_order_view')
    #     return {
    #         'type': 'ir.actions.act_window',
    #         'name': 'Payment Vouchers',
    #         'res_model': 'cash.order',
    #         'view_type': 'form',
    #         'view_mode': 'tree,form',
    #         'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
    #         'domain': [('commission_request_ids', '=', self.id)],

    #     }
                 
'''
class RealEstateContract(models.Model):

    _inherit = 'realestate.contract.model'

    def start_contract(self):
        for rec in self:
            super(RealEstateContract, rec).start_contract()
            _logger.info('*************************************************************jjjjjjjjjjjjjjjjjjjjj')
            sales_contracts=self.env['real.estate.sale'].search([('contract_id','=', rec.id)])
            _logger.info(sales_contracts)
            _logger.info(rec.payment_ids)
            if sales_contracts:
                sales_contracts.write({'payment_ids':[(4,payment.id ) for payment in rec.payment_ids]})

'''