# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime,timedelta
import operator
import re
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, AccessError,UserError


class ContractTypeTerms(models.Model):

    _name = "hr.contract.term"
    _description = 'Contract Terms'
    _order = 'term_no'

    name = fields.Char(string='Term' ,required=True)
    term_no = fields.Integer("Term Number", required=True)
    description = fields.Text('Description')
    type = fields.Selection([
        ('mandatory', 'Mandatory'),
        ('optional', 'Optional')], string='Type', default='mandatory', required=True)



class RealEstateContract(models.Model):
    _name = 'realestate.contract.model'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Contract'
    _rec_name = 'contract_no'

    contract_no = fields.Char('Contract No')
    contract_type = fields.Selection([('all_property','All property'),('specific_units','Specific Units')],string="Contract Type", tracking=True)
    name = fields.Char(related="contract_no", string='Name')
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", oldname='currency')
    contract_amount = fields.Monetary(string='Contract Amount', tracking=True, store=True)
    contract_paid_amount = fields.Monetary(string='Paid Amount', compute='_compute_contract_payments', tracking=True, store=True)
    partner_id=fields.Many2one("res.partner", string="Customer" , ondelete="cascade", tracking=True)
    investor_id=fields.Many2one("res.partner", string="Investor" , ondelete="cascade", tracking=True)
    property_id=fields.Many2one( comodel_name='real.estate', string='Property Name', tracking=True)
    unit_id= fields.Many2one('real.estate.units',string='Unit', required=False, tracking=True)
    property_type = fields.Selection('real.estate', related='unit_id.property_type')
    representative_id=fields.Many2one("res.partner", string="Company representative", tracking=True, ondelete="cascade")

    investment_type = fields.Selection([('shares','Shares'),('land','Land Purchase')],string="Investment Type", tracking=True)
    commission_type= fields.Selection([('fixed','Fixed'),('ratio','Ratio')], default='fixed', string="Type", tracking=True)
    share_amount= fields.Float(string="Amount/ Percent", tracking=True)
    shares = fields.Integer(string='Number of Shares', tracking=True)
    sign_date = fields.Date('Signing date', tracking=True)
    month_amount = fields.Monetary(string='Monthly Compensation Amount', tracking=True)
    investment_amount = fields.Monetary(string='Investment Amount', readonly=True, compute='calculate_investment_amount', tracking=True)
    land_amount = fields.Monetary(string='Land Purchase Amount', tracking=True)
    land_tax = fields.Float(string='Land Taxes', tracking=True)
    land_com = fields.Float(string='Land Commission', tracking=True)
    land_prof = fields.Float(string='Land Profite', tracking=True)
    land_cost = fields.Float(string='Land Cost', readonly=True, compute='calculate_land_amount', tracking=True)
    investor_ratio = fields.Float(string="Investor Ratio", digits=(16, 2), tracking=True)
    company_ratio = fields.Float(string="Company Ratio", digits=(16, 2), tracking=True)

    investor_clearance_id = fields.Many2one('investor.clearance')

    date = fields.Date(string=' Date ', tracking=True)
    notify_date = fields.Date(string='Notify Date', tracking=True)
    date_start = fields.Date(string='Start Date ', tracking=True)
    date_end = fields.Date(string='End Date', tracking=True)
    evacuation_date = fields.Date(string='Evacuation Date', tracking=True)
    delivery_date = fields.Date(string='Delivery Date', tracking=True)
    sign_date = fields.Date(string='Signing date', tracking=True)
       
    state = fields.Selection(selection=[
        ('draft','Draft'),
        ('finance', 'Finance'), 
        ('confirmed', 'Confirmed'), 
        #('expired', 'Expired'),
        ('done','Done')
        ], default='draft', tracking=True)
    attachment =fields.Many2one('ir.attachment', string='Copy', tracking=True)
    payment_ids = fields.One2many('rent.contract.payment', 'analytic_id', 'Payments')
    

    company_id = fields.Many2one('res.company',readonly=True, string='Company', default=lambda self: self.env.user.company_id)
    monthly_rental = fields.Monetary('Monthly rental amount', required=False, tracking=True)
    # fields used for renting contracts and may be deleted later on

    term_ids = fields.Many2many('hr.contract.term', )
    

    duration_nums = fields.Integer(string="Duration")
    duration_option = fields.Selection([('day','Days'),('month','Months'),('year','Years')],default='month')
    contract_partner_type = fields.Selection(selection=[('sale','Sale'),('rent','Rent'),('investment','Investment')], required=True, tracking=True, default='sale', string='Partner Contract Type')

    contract_template_id = fields.Many2one(string='Contract Template',
                                           comodel_name='realestate.contract.template',
                                           readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    sale_unit_id = fields.Many2one('real.estate.sale', tracking=True)
    investment_request_ids = fields.Many2one('cash.receive', tracking=True)
    is_transfer = fields.Boolean('Transfer to Project', default=False, tracking=True)
    is_cleared = fields.Boolean('Clearing Status', default=False, tracking=True)
    transfer_amount = fields.Float('Transfer Amount', tracking=True)
    investor_contract = fields.Many2one('investor.clearance', tracking=True)
    commission_sale_lines = fields.One2many(comodel_name='sale.commission', inverse_name='sale_id')
    commission = fields.Monetary(string='Commission', tracking=True)
    clearance_type = fields.Selection([
                                ('complete', 'Full Clearance'),
                                ('share', 'Shares Clearance'),
                                ('capital', 'Capital Clearance'),
                                ('profit', 'Profit Clearance'),
                                ('trans', 'Transfer to Another Project'),],
                                'Clearance Type', tracking=True)
    line_ids = fields.One2many('clearance.history.line', 'line_id', readonly=True)    
    # compute='calculate_commission'

    def calculate_commission(self):
        for rec in self:
            if len(rec.commission_sale_lines.ids):
                rec.commission = sum(rec.commission_sale_lines.mapped('amount'))
                # if rec.commission > rec.property_commission and rec.property_commission!=0:
                #     raise ValidationError(_('total of commission must not be more than %s' % rec.property_commission))
            else:
                rec.commission =0

    @api.onchange('contract_partner_type')
    def _onchange_contract_partner_type(self):
        """Update the domain of partner_id based on the selected contract_partner_type.

        """
        if self.contract_partner_type == 'investment':
            domain = [('partner_type', '=', 'investor')]
        else:
            domain = [('partner_type', '=', 'owner')]
        
        return {'domain': {'partner_id': domain}}

    @api.depends('land_amount', 'land_tax', 'land_com', 'land_prof')
    def calculate_land_amount(self):
        for rec in self:
            rec.land_cost = rec.land_amount + rec.land_tax + rec.land_com + rec.land_prof

    @api.depends('commission_type', 'share_amount', 'shares')
    def calculate_investment_amount(self):
        for rec in self:
            if rec.commission_type == 'fixed':
                rec.investment_amount = rec.share_amount * rec.shares
            elif rec.commission_type == 'ratio':
                if rec.shares != 0:  # To avoid division by zero error
                    rec.investment_amount = rec.share_amount / rec.shares
                else:
                    rec.investment_amount = 0
            else:
                rec.investment_amount = 0

    @api.onchange('contract_template_id')
    def _onchange_contract_template_id(self):
        """
        Update contract clauses from selected contract template, and reset the template to False
        Clauses are used in printed contract reports.
        """
        for contract in self:
            if not contract.contract_template_id:
                continue

            # This will accumulate clauses from the template and the contract itself.
            # Check UX feedback to see if this is the desired behavior.
            contract.clause_ids = [(0, 0, {
                'name': clause.name,
                'content': clause.content,
                'sequence': clause.sequence,
            }) for clause in contract.contract_template_id.clause_ids.sorted(key=lambda l: l.sequence)]

            # Reset the template to False
            contract.contract_template_id = False

    clause_ids = fields.One2many(string='Clauses',
                                 comodel_name='realestate.contract.clause',
                                 inverse_name='contract_id',
                                 readonly=True, states={'draft': [('readonly', False)]}, copy=True)
    delegate_id = fields.Many2one('real.estate.delegate')

    @api.onchange('property_id', 'contract_partner_type')
    def _onchange_unit_id(self):
        """ Update the domain of unit_id based on the selected
            contract_type, property_id, and contract_partner_type.

        """
        if self.property_id:
            print("@@@@@@@@ 1 @@@@@@@@")
            print(f'Property ID: {self.property_id.id}, Contract Partner Type: {self.contract_partner_type}')
            if self.contract_partner_type == 'sale':
                unit_domain = [
                    ('base_property_id', '=', self.property_id.id),
                    ('state', '=', 'available')
                ]
            elif self.contract_partner_type == 'rent':
                print("@@@@@@@@ 2 @@@@@@@@")

                unit_domain = [
                    ('base_property_id', '=', self.property_id.id),
                    ('state', '=', 'available'),
                    ('property_type', '=', 'ready')
                ]
            else:
                unit_domain = []
            print(f'Unit Domain: {unit_domain}')
            return {'domain': {'unit_id': unit_domain}}
        else:
            return {'domain': {'unit_id': []}}

        # res = {'domain': {'unit_id': [('base_property_id', '=', self.property_id.id)]}}

        # if self.contract_partner_type == 'sale':
        #     res['domain']['unit_id'].append(('state', '=', 'available'))
        # elif self.contract_partner_type == 'rent':
        #     res['domain']['unit_id'].append(('state', '=', 'available'))
        #     res['domain']['unit_id'].append(('property_type', '=', 'ready'))
        # elif self.contract_partner_type == 'resale':
        #     res['domain']['unit_id'].append(('state', '=', 'delegated'))
        #     delegate = self.env['real.estate.delegate'].search([
        #         ('partner_id', '=', self.partner_id.id),
        #         ('unit_id', '=', self.unit_id.id)
        #     ], limit=1)
        #     self.delegate_id = delegate.id if delegate else False

        # return res

    @api.onchange('date_start')
    def onchange_warranty_beggining(self):
        if self.date_start:
            self.date_end = self.date_start+ relativedelta(years=1)

    @api.onchange('date_start')
    def _onchange_date_start(self):
        if self.date_start:
            if fields.Date.from_string(self.date)  < fields.date.today() and \
                not self.env.user.has_group('rent_contract.rent_with_previous_date'):
                raise UserError(_('Sorry! You cannot register this contract with previous date unless you have the privilige to do this.'))
            
    def unlink(self):
        for record in self:
            if record.state not in ('draft'):
                raise UserError(_('Sorry! You cannot delete contract not in Draft state.'))
        return models.Model.unlink(self)

    @api.model
    def get_seq_to_view(self):
        sequence = self.env['ir.sequence'].search([('code', '=', self._name)])
        return sequence.get_next_char(sequence.number_next_actual)

    
    @api.depends('contract_no')
    def g_name(self):
        if self.contract_no and self.unit_id.unit_name:
            self.name = self.contract_no +','+ self.unit_id.unit_name

    @api.model
    def _create_payment(self,amount,due_date):
        self.write({'payment_ids': [(0,0, {
            'name': 'new',
            'pay_amount': amount,
            'paid_amount': 0.0,
            'due_date': due_date ,
            'state': 'draft',
            'analytic_id': self.id,
             }
             )]})

    
    '''
    @api.onchange('payment_rate')
    def _onchange_payment_rate(self):
        """Update the contract fields with that of payment rate.
        """
        contract = self.payment_rate
        if not contract:
            return
        for field_name, field in contract._fields.items():
            if not any((
                field.compute, field.related, field.automatic,
                field.readonly, field.company_dependent,
            )):
                self[field_name] = self.payment_rate[field_name]


    
    
    @api.onchange('contract_type')
    def _onchange_contract_type(self):
        res = {}
        if self.contract_type=='all_property':
            res['domain']={'property_id':[('state', '=', '0')]}
        else: 
            res['domain']={'property_id':[('state', '=', ('0','partial_rented'))]}
        return res

    @api.constrains('duration_nums')
    def _check_duration_nums(self):
        if self.duration_nums<=0:
            raise ValidationError(
                    _("Duration nums must be greater than zero") 
                )
    def end_contract(self):
        state = 'expired'
        for payment_id in self.payment_ids:
            if payment_id.state in ['draft','partialy_paid']  :
                state = 'hanging'
        self.state = state

    '''

    @api.onchange('property_id')
    def _onchange_property(self):
        res = {}
        res['domain']={'unit_id':[('base_property_id', '=', self.property_id.id),('state','=','0')]}
        return res


    @api.constrains('partner_id')
    def _check_partner_id_recurring_invoices(self):
        if self.contract_partner_type != 'investment':
            for contract in self:
                if not contract.partner_id:
                    raise ValidationError(
                        _("You must supply a tenant for the contract '%s'") %
                        contract.name
                    )
    
    @api.constrains('date_end','date_start')
    def _check_release_date(self):
        for rec in self:
            # OR if it starts between the given dates
            # OR if it starts before the date_start and finish after the date_end (or never finish)
            clause_final = [('id','!=',rec.id),('property_id', '=', rec.property_id.id), ('state', '=', 'valid')] 
            if rec.unit_id:
                clause_4 = [ ('unit_id', '=', rec.unit_id.id)]
                clause_final += clause_4
            contreacts = self.env['realestate.contract.model'].search(clause_final)
            if contreacts:
                raise UserError(_('Sorry! You cannot open  contract in this property .'))


    @api.constrains('date')
    def _check_date_invoices(self):
        if self.contract_partner_type != 'investment':
            for contract in self:
                if not contract.date:
                    raise ValidationError(
                        _("You must supply a date for contract "))

    @api.depends('payment_ids')
    def _compute_contract_payments(self):
        for rec in self:
                total = sum(self.payment_ids.mapped('pay_amount'))
                rec.contract_paid_amount = total

    def action_review(self):
        if self.investment_type != 'shares':
            if not self.payment_ids:
                raise ValidationError(
                            _("Please create payment"))

            for contract in self:
                total = sum(self.payment_ids.mapped('pay_amount'))
                self.contract_paid_amount = total
                if self.investment_type == 'land':
                    if contract.land_cost != total:
                        raise UserError(_("Invalid amount. Please ensure that the total of scheduled payments matches the and Purchase amount."))
                elif contract.contract_amount != total:
                    raise UserError(_("Invalid amount. Please ensure that the total of scheduled payments matches the contract amount."))


            if self.payment_ids and sum(self.payment_ids.mapped('pay_amount')) < self.contract_amount:
                raise ValidationError(
                            _("Please create payments, contract payment must be equals to contract total amount"))
        return self.write({'state': 'finance'})
  
    def start_contract(self):
        if self.investment_type != 'shares':
            if not self.payment_ids:
                raise ValidationError(
                            _("Please create payment"))

            if self.contract_partner_type == 'sale':
                self.unit_id.write({'owner_id': self.partner_id.id})
                for rec in self:
                        contract = rec.env['real.estate.sale'].create({
                        'unit_id':rec.unit_id.id,
                        'partner_id':rec.partner_id.id,
                        'amount':rec.contract_amount,
                        'date': rec.date,
                        'real_estate_id':rec.unit_id.base_property_id.id,
                        'real_notify_date':rec.notify_date,
                        'evacuation_date':rec.evacuation_date,
                        'delivery_date':rec.delivery_date,
                        'customer_type':'normal',
                        'sale_type':'sale'
                        })
                rec.sale_unit_id = contract.id
                self.unit_id.write({'state': 'sold', 'owner_id':self.partner_id.id})
        
        if self.contract_type == 'all_property':
            if self.property_id:
                self.property_id.contract_id=self.id

        elif self.unit_id:
           self.unit_id.contract_id = self.id

        if self.contract_partner_type == 'investment':
            if self.property_id:
                if self.investment_type == 'shares':
                    investor_vals = {
                                    'name': self.partner_id.id,
                                    'commission_type': self.commission_type,
                                    'commission_amount': self.share_amount,
                                    'shares': self.shares,
                                    'sign_date': self.sign_date,
                                    'deliver_date': self.delivery_date
                                }
                    self.property_id.write({'investors_ids': [(0, 0, investor_vals)]})

                    if self.is_transfer == True and self.investment_amount > self.transfer_amount:
                        payment_id = self.env['cash.receive'].create({
                                'state':'draft',
                                'date': self.date,
                                'partner_id': self.partner_id.id,
                                'amount': self.investment_amount - self.transfer_amount,
                                'disc' : self.contract_no + ' ' + 'سند قبض من عقد إستثمار عقاري رقم',
                                'investment_request_ids' : self.id,
                            })

                    if self.is_transfer == False:
                        payment_id = self.env['cash.receive'].create({
                                'state':'draft',
                                'date': self.date,
                                'partner_id': self.partner_id.id,
                                'amount': self.investment_amount,
                                'disc' : self.contract_no + ' ' + 'سند قبض من عقد إستثمار عقاري رقم',
                                'investment_request_ids' : self.id,
                            })
                    self.investment_request_ids = payment_id.id

        if self.contract_partner_type == 'rent':
            self.unit_id.write({'state': 'rent', 'renter_id':self.partner_id.id})

        self.write({'state':'confirmed'})

    def action_end_rent(self):
        if self.contract_partner_type == 'rent':
            self.unit_id.write({'state': 'available'})
        return self.write({'state': 'done'})

    def action_payment_receive(self):
    
        tree_view = self.env.ref('cash_request.cash_receive_tree_view')
        form_view = self.env.ref('cash_request.cash_receive_view')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Receipt Vouchers',
            'res_model': 'cash.receive',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('investment_request_ids', '=', self.id)],

        }


    def open_sale(self):
        domain = [ ('id', '=',self.sale_unit_id.id)]
        res_id = self.sale_unit_id.id  or False     
        return {
          'name': _('Sales'),           
          'domain': domain,          
          'res_model': 'real.estate.sale', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form,kanban',
          'help': _('''<p class="oe_view_nocontent_create">
           
                                    Attach
    documents of your employee.</p>'''),
         'limit': 80,
         'context': "{'default_res_model': '%s','default_res_id': %d}"% ('real.estate.sale', res_id)}
   
    def set_to_draft_contract(self):
        self.payment_ids.unlink()
        self.click_pay = False
        if self.contract_type=='all_property':
            if self.property_id:
                self.property_id.contract_id=False
                #self.property_id.renter_id = False
                #self.property_id.state = '0'
        elif self.unit_id:
            self.unit_id.contract_id=False
        self.write({'state':'draft'})

  
    def restart_contract(self):
        #self.click_pay = False
        self.write({'state':'draft'})

    @api.model   
    def create(self, vals):
      
        # contract = self.search([('unit_id','=',vals['unit_id']),('unit_id','!=',False)])
        # if contract:
        #     raise UserError(_('Sorry! You cannot open  contract in this property .'))
        vals['contract_no'] = self.env['ir.sequence'].sudo().next_by_code('realestate.contract.model') or '/'

        return super(RealEstateContract, self).create(vals)

class ClearanceHistory(models.Model):

    _name = 'clearance.history.line'
    _description = 'Clearance History'
    _rec_name='line_id'

    line_id = fields.Many2one('realestate.contract.model')
    name = fields.Char(string="Name", tracking=True)
    date = fields.Date(string=' Date ', tracking=True)
    investor_ratio = fields.Float(string="Investor Ratio", digits=(16, 2), tracking=True)
    shares = fields.Integer(string='Number of Shares', tracking=True)
    investment_amount = fields.Monetary(string='Investment Amount', tracking=True)
    share_amount= fields.Float(string="Amount/ Percent", tracking=True)
    commission_type= fields.Selection([('fixed','Fixed'),('ratio','Ratio')], string="Type", tracking=True)
    profit = fields.Float(string="Project Profit", tracking=True)
    clearance_amount = fields.Float(string="Clearance Amount", tracking=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency")
    clearance_type = fields.Selection([
                                ('complete', 'Full Clearance'),
                                ('shares', 'Shares Clearance'),
                                ('capital', 'Capital Clearance'),
                                ('profit', 'Profit Clearance'),
                                ('trans', 'Transfer to Another Project'),],
                                'Clearance Type',)
    state = fields.Selection([('draft', 'Draft'),
                              ('finance', 'Financial approval'),
                              ('investment', 'Investment approval'),
                              ('general', 'General approval'),
                              ('approved', 'Approved'),],
                             'State')


class SaleCommission(models.Model):

    _name = 'sale.commission'

    sale_id = fields.Many2one('realestate.contract.model', string='Contract')
    partner_id = fields.Many2one(
        'res.partner',
        'partner',
        required=True,
        )
    journal_id = fields.Many2one('account.journal', tracking=True)
    amount = fields.Monetary(string="Amount", required=True, default= lambda self: self.sale_id.property_id.commission_amount)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",default=lambda self: self.env.company.currency_id.id)
    account_id = fields.Many2one('account.account', tracking=True)
    check = fields.Boolean("Payment Created?", readonly=True)
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    sale_commission_type = fields.Selection([
                            ('shares', 'Shares Commission'),
                            ('Land', 'Land Commission'),],
                            'Commission Type', default='shares', tracking=True)

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


class ProjectContractTemplate(models.Model):
    _name = 'realestate.contract.template'
    _description = 'Project Contract Template'
    _order = 'sequence, id'
    _check_company_auto = True

    sequence = fields.Integer(string='Sequence', required=True, default=1)
    active = fields.Boolean(default=True)

    name = fields.Char(string='Title', required=True, translate=True)
    clause_ids = fields.One2many(string='Clauses',
                                 comodel_name='realestate.contract.template.line',
                                 inverse_name='template_id',
                                 required=True, translate=True)
    company_id = fields.Many2one(string='Company',
                                 comodel_name='res.company',
                                 required=True, default=lambda self: self.env.company)

class ProjectContractTemplateLine(models.Model):
    _name = 'realestate.contract.template.line'
    _description = 'Project Contract Template Clauses'
    _order = 'sequence, id'
    _check_company_auto = True

    sequence = fields.Integer(string='Sequence', required=True, default=1)
    active = fields.Boolean(default=True)

    name = fields.Char(string='Title', required=True, translate=True)
    content = fields.Html(string='Content', required=True, translate=True)
    template_id = fields.Many2one(string='Template',
                                    comodel_name='realestate.contract.template',
                                    required=True, ondelete='cascade')

    company_id = fields.Many2one(related='template_id.company_id', store=True, readonly=True)   

class ProjectContractClause(models.Model):
    _name = 'realestate.contract.clause'
    _description = 'Project Contract Legal Clauses'
    _order = 'sequence, id'
    _check_company_auto = True

    sequence = fields.Integer(string='Sequence', required=True, default=1)
    active = fields.Boolean(default=True)

    name = fields.Char(string='Title', required=True, translate=True)
    content = fields.Html(string='Content', required=True, translate=True)
    contract_id = fields.Many2one(string='Contract',
                                  comodel_name='realestate.contract.model',
                                  required=True, ondelete='cascade')
    company_id = fields.Many2one(related='contract_id.company_id', store=True, readonly=True) 


class contract_archive(models.Model):
    _name = 'contract.archive'

    start = fields.Date(string="Start Date",required=True)
    end = fields.Date(string="End Date",required=True)
    contract_id = fields.Many2one(
        string="Contract",
        comodel_name="realestate.contract.model",
    )

class AccountAnalyticAccountPayment(models.Model):
    _name = 'rent.contract.payment'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char(string="Payment No", readonly=True, copy=False, default='/')
    pay_amount = fields.Float('Payment Amount', tracking=True)
    paid_amount = fields.Float('Paid Amount', tracking=True)
    pay_date = fields.Date('Payment Date', tracking=True)
    due_date = fields.Date('Due Date', tracking=True)
    refues_reason = fields.Char(string="Refues Reason", readonly=True, tracking=True)
    refues_date = fields.Date(string="Refues Date", readonly=True, tracking=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('review','Review'),
        ('confirmed','Confirmed'),
        ('partialy_paid','Partialy Paid'),
        ('paid', 'Paid'), 
        ('post', 'Post Paid'),
        ('refused','refused')], default='draft',string="Status", tracking=True)
    analytic_id = fields.Many2one('realestate.contract.model', 'Contract', readonly=True, tracking=True)
    
    tax_amount = fields.Integer(string="Tax amount", tracking=True)

    next_remain = fields.Float('Next Payment Remain Amount', tracking=True)
    saltat_bool = fields.Boolean()
    unit_id = fields.Many2one('real.estate.units', related='analytic_id.unit_id',
        string="Unit", store=True, tracking=True)
    property_id = fields.Many2one('real.estate', related="analytic_id.property_id",
        string="Property", store=True, tracking=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id, ondelete='restrict')
    renter_id  = fields.Many2one('res.partner',related="analytic_id.partner_id",
        string="Renter", store=True, tracking=True)
    user_ids = fields.Many2many(
        string="Users",
        comodel_name="res.users",
        related='property_id.user_ids'
    )
    supervisor_id = fields.Many2one(related='property_id.supervisor_id',string="Supervisor", store=True)
    related_payment_ids = fields.One2many(
        string="payments",
        comodel_name="rent.contract.payment",
        inverse_name="payment_id",
        readonly=True,
    )
    payment_id = fields.Many2one(
        string="Payment",
        comodel_name="rent.contract.payment",
    )
    
    payment_state = fields.Selection(
        string="Payment State",
        selection=[
                ('previous', 'Previous'),
                ('current', 'Current'),
                ('future', 'Future'),
        ],required=True , default="current"
    )
    payment_type = fields.Selection(
        string="Payment Type",
        selection=[
                ('cash', 'Cash'),
                ('transfer', 'Bank Transfer'),
                ('check', 'Check'),
        ],required=True , default="cash"
    )
    check_number = fields.Char(string="Check Number", )
    note = fields.Text(string="note")
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')
    move_id = fields.Many2one('account.move', 
        string='Move',
        required=False,
        tracking=True
    )
    journal_id = fields.Many2one('account.journal',
        string='Journal',
        domain="[('type', 'in', ('cash','bank'))]",
        tracking=True
    )
    account_id = fields.Many2one('account.account',
        string='Account',
        tracking=True
    )
    account_analytic_id = fields.Many2one('account.analytic.account',
        string='Cost Center',
        tracking=True
    )

    # @api.onchange('property_id')
    # def _onchange_property_id(self):
    #     """Update the domain of unit_id based on the selected property.

    #     """
    #     domain = [('base_property_id', '=', self.property_id.id)]
    #     return {'domain': {'unit_id': domain}}
    
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'rent.contract.payment'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for payment_id in self:
            payment_id.attachment_number = attachment.get(payment_id.id, 0) 

    def return_to_paid(self):
        self.write({
            'state':'paid'
        })

    

    # @api.model   
    # def create(self, vals):
    #     vals['name'] = self.env['ir.sequence'].next_by_code('rent.contract.payment') or '/'       
    #     result = super(AccountAnalyticAccountPayment, self).create(vals)       
    #     return result

    # @api.model
    # def get_seq_to_view(self):
    #     sequence = self.env['ir.sequence'].search([('code', '=', self._name)])
    #     return sequence.get_next_char(sequence.number_next_actual)

  
    def unlink(self):
        for record in self:
            if record.state not in ('draft'):
                raise UserError(_('Sorry! You cannot delete payment not in Draft state.'))
        return models.Model.unlink(self)

    def set_to_draft(self):
        for payment_id in self.related_payment_ids:
            if payment_id.state != 'draft':
                raise UserError(_('Sorry! You cannot Edit Payment that related with other payment not on draft state please parse them first.'))
        self.related_payment_ids.unlink()
        self.state = 'draft'
        self.paid_amount = 0.0

    
    def confirm_payment(self):
        if self.analytic_id.state != 'confirmed':
            raise ValidationError(_("contract of this payment is not valid"))

        else:
            self.due_date = self.pay_date
            for payment in self.filtered('pay_amount'):
               
                if  round(abs(payment.paid_amount),2) > round(abs(payment.pay_amount),2) :
                    raise ValidationError(
                        _("Paid '%s' amount can't be greater than payment amount")
                        % payment.name
                    )
            if round(abs(payment.paid_amount),2) < round(abs(payment.pay_amount),2) and not self.pay_ids:
                self.saltat_bool = True
                self.pay_ids.create({

                    'p_id':self.id,
                    'remain_am':self.pay_amount - self.paid_amount,
                    'state':'draft',
                    })
                self.state = 'partialy_paid'

            if round(abs(payment.paid_amount),2) == round(abs(payment.pay_amount),2) :
                self.state = 'paid'


    # @api.constrains('paid_amount')
    # def _check_paid_amount(self):
    #     """
    #     Added constraint to update the state based on paid_amount and pay_amount.
    #     """
    #     for record in self:
    #         if round(record.paid_amount, 2) == round(record.pay_amount, 2):
    #             record.state = 'paid'
    #         elif round(record.paid_amount, 2) > round(record.pay_amount, 2):
    #             raise ValidationError(_("Paid amount can't be greater than the payment amount."))
    #         else:
    #             if record.state == 'paid':
    #                 record.state = 'partialy_paid'
    # def _write_paid_state(self):
    #     for payment in self.filtered('paid_amount'):
    #         if round(abs(payment.paid_amount),2) == round(abs(payment.pay_amount),2):
    #             payment.write({'state':'paid'})
    
    
    def attachment_tree_view(self):
        domain = ['&', ('res_model', '=', 'rent.contract.payment'), ('res_id', 'in',self.ids)]
        res_id = self.ids and self.ids[0] or False     
        return {
          'name': _('Attachments'),           
          'domain': domain,          
          'res_model': 'ir.attachment', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form,kanban',
          'view_type': 'form',
          'help': _('''<p class="oe_view_nocontent_create">
                        Attach Rent Contract Payment Documents.</p>'''),
         'limit': 80,
         'context': "{'default_res_model': '%s','default_res_id': %d}"% (self._name, res_id)}

class payment_confirmation_wiz(models.TransientModel):
    _name = 'payemnt.confirmation.wiz'

    amount = fields.Float(string='Amount',required=True)
    payemnt_date =  fields.Date(
        string='Payemnt Date',
        default=fields.Date.today(),
    )
  
    payment_state = fields.Selection(
        string="Payment State",
        selection=[
                ('previous', 'Previous'),
                ('current', 'Current'),
                ('future', 'Future'),
        ],required=True , default="current"
    )
    payment_type = fields.Selection(
        string="Payment Type",
        selection=[
                ('cash', 'Cash'),
                ('transfer', 'Bank Transfer'),
                ('check', 'Check'),
        ],required=True , default="cash"
    )
    check_number = fields.Char(string="Check Number", )
    journal_id= fields.Many2one('account.journal',domain=[('type','in',('cash','bank'))])
    note = fields.Text(string="Note")

    def close_parent_payments(self , payment_id):
        if payment_id.payment_id:
            if payment_id.payment_id.state != 'post':
                payment_id.payment_id.state = 'paid'
            return self.close_parent_payments(payment_id.payment_id)
    
    def check_contract(self , contract_id):
        flag = True
        for payment_id in contract_id.payment_ids:
            if payment_id.state in ['draft','partialy_paid']:
                flag = False
        if flag :
            contract_id.state = 'expired'   
                 
    
    # def confirm_payment(self):
    #     """
    #     Modified the state change logic here to avoid redundancy with the _check_paid_amount constraint.
    #     """
    #     if self.analytic_id.state != 'confirmed':
    #         raise ValidationError(_("Contract of this payment is not valid"))
    #     else:
    #         self.due_date = self.pay_date
    #         for payment in self.filtered('pay_amount'):
    #             if round(abs(payment.paid_amount), 2) > round(abs(payment.pay_amount), 2):
    #                 raise ValidationError(_("Paid '%s' amount can't be greater than payment amount") % payment.name)
    #             if round(abs(payment.paid_amount), 2) < round(abs(payment.pay_amount), 2):
    #                 self.saltat_bool = True
    #                 self.related_payment_ids.create({
    #                     'payment_id': self.id,
    #                     'pay_amount': self.pay_amount - self.paid_amount,
    #                     'state': 'draft',
    #                     })
    #                 self.state = 'partialy_paid'
                # if round(abs(payment.paid_amount), 2) == round(abs(payment.pay_amount), 2):
                    # self.state = 'paid'

        # payment_id =self._context.get('active_id', False)
        # payment_id = self.env['rent.contract.payment'].browse(payment_id)
        # if payment_id.analytic_id.state not in ['confirmed','hanging']:
        #     raise ValidationError(_("contract of this payment is not valid"))
        # else:
        #     payment_id.pay_date = fields.date.today()
        #     if round(self.amount,2) > round(payment_id.pay_amount , 2):
        #         raise ValidationError(_("Payment amount is more than contract amount"))
        #     elif self.amount <= 0.0 :
        #         raise ValidationError(_("Payment amount is must be more than zero"))
        #     elif round(self.amount,2) < round(payment_id.pay_amount , 2):
        #         self.env['rent.contract.payment'].create({
        #             'name':payment_id.name +"/1",
        #             'property_id':payment_id.property_id.id,
        #             'unit_id':payment_id.unit_id.id,
        #             'supervisor_id':payment_id.supervisor_id.id,
        #             'renter_id':payment_id.renter_id.id,
        #             'analytic_id':payment_id.analytic_id.id,
        #             'due_date':payment_id.due_date,
        #             'pay_amount':round(payment_id.pay_amount,2) - round(self.amount,2) ,
        #             'payment_id':payment_id.id,
        #             'state':'draft',
        #         })
        #         payment_id.write({
        #             'paid_amount' : round(self.amount,2),
        #             'state' : 'partialy_paid',
        #             'payment_state':self.payment_state,
        #             'payment_type':self.payment_type,
        #             'check_number':self.check_number,
        #             'note':self.note,
        #             'pay_date':self.payemnt_date,
        #         })
        #     elif round(self.amount,2) == round(payment_id.pay_amount,2):
        #         self.close_parent_payments(payment_id)
        #         payment_id.write({
        #             'state' : 'paid',
        #             'paid_amount' : self.amount,
        #             'payment_state':self.payment_state,
        #             'payment_type':self.payment_type,
        #             'check_number':self.check_number,
        #             'note':self.note,
        #             'pay_date':self.payemnt_date,
        #         })
        # if payment_id.analytic_id :
        #     self.check_contract(payment_id.analytic_id)

