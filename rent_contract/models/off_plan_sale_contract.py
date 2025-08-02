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

    contract_no = fields.Char('Contract No')
    contract_type = fields.Selection([('all_property','All property'),('specific_units','Specific Units')],string="Contract Type")
    name = fields.Char(related="contract_no", string='Name') 
    unit_id= fields.Many2one('real.estate.units',string='Unit',required=False,)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", oldname='currency')
    contract_amount = fields.Monetary(string='Contract Amount')
    partner_id=fields.Many2one("res.partner", string="Tenant" , ondelete="cascade")
    property_id=fields.Many2one(
        comodel_name='real.estate',
        string='Property Name')

    #owner=fields.Many2many(related='property_id.owner_ids',string='Owners', domain=[('partner_type','=','owner')],  context="{'default_partner_type': 'owner'}", ondelete="cascade",store=True)
    representative_id=fields.Many2one("res.partner", string="Company representative" , ondelete="cascade")
    date = fields.Date(
        string=' Date ',
        required=True
    )
    notify_date = fields.Date(string='Notify Date', )

    date_start = fields.Date(
        string='start Date ',
        
    )
    date_end = fields.Date(string='end Date', )
       
    state = fields.Selection(selection=[
        ('draft','Draft'),
        ('confirmed', 'Confirmed'), 
        #('expired', 'Expired'),
        #('done','Done')
        ], default='draft')
    attachment =fields.Many2one('ir.attachment', string='Copy')
    payment_ids = fields.One2many('rent.contract.payment', 'analytic_id', 'Payments')
    
    
    
    delivery_date = fields.Date(string="Delivery Date")
    company_id = fields.Many2one('res.company',readonly=True, string='Company', default=lambda self: self.env.user.company_id)
    monthly_rental = fields.Monetary('Monthly rental amount', required=False)
    # fields used for renting contracts and may be deleted later on

    term_ids = fields.Many2many('hr.contract.term', )
    

    duration_nums = fields.Integer(string="Duration")
    duration_option = fields.Selection([('day','Days'),('month','Months'),('year','Years')],default='month')
    
    
    
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
        for contract in self:
            if not contract.date:
                raise ValidationError(
                    _("You must supply a date for contract "))

  
    def start_contract(self):
        if not self.payment_ids:
            raise ValidationError(
                        _("Please create payment"))

        if self.payment_ids and sum(self.payment_ids.mapped('pay_amount')) < self.contract_amount:
            raise ValidationError(
                        _("Please create payments, contract payment must be equals to contract total amount"))
        '''
        self.invoice_id = self.env['account.move'].create({
            'partner_id':self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'move_type':'out_invoice',
            'invoice_line_ids':
            [(0, None, {
                        'name': 'Contract' +  self.name or '',
                        'price_unit':  self.contract_amount,
                        'quantity': 1.0,
                        'account_id': self.income_account_id.id,
                    }),
            ]
            })
        '''
        #self.invoice_id.post()
        if self.contract_type == 'all_property':
            if self.property_id:
                self.property_id.contract_id=self.id
                #self.property_id.renter_id = self.partner_id.id
                #self.property_id.unit_ids.state='rented'
                #self.property_id.state = 'rented'

        elif self.unit_id:
           self.unit_id.contract_id = self.id
           #self.unit_id.renter_id = self.partner_id.id
           #self.unit_id.state = 'rented'
           #self.property_id.property_rented_units_number+=1
           #if self.property_id.property_rented_units_number<self.property_id.property_units_number:
           #     self.property_id.state='partial_rented'

        self.write({'state':'confirmed'})

    
    

   
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
            #self.unit_id.renter_id = False
            #self.unit_id.state = '0'
 
            #self.property_id.property_rented_units_number-=1
            #print("self.property_id.property_rented_units_number",self.property_id.property_rented_units_number)
            #if self.property_id.property_rented_units_number<self.property_id.property_units_number:
            #    self.property_id.state='partial_rented'
            #if self.property_id.property_rented_units_number==0:
            #    self.property_id.write({'state':'0'})
        self.write({'state':'draft'})

  
    def restart_contract(self):
        #self.click_pay = False
        self.write({'state':'draft'})

    @api.model   
    def create(self, vals):
      
        contract = self.search([('unit_id','=',vals['unit_id']),('unit_id','!=',False)])
        if contract:
            raise UserError(_('Sorry! You cannot open  contract in this property .'))
        vals['contract_no'] = self.env['ir.sequence'].sudo().next_by_code('realestate.contract.model') or '/'

        return super(RealEstateContract, self).create(vals)       

   
   

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
    pay_amount = fields.Float('Payment Amount', required=True)
    paid_amount = fields.Float('Paid Amount')
    pay_date = fields.Date('Payment Date')
    due_date = fields.Date('Due Date')
    refues_reason = fields.Char(string="Refues Reason", readonly=True)
    refues_date = fields.Date(string="Refues Date", readonly=True)
    state = fields.Selection(selection=[
        ('draft', 'Draft'),
        ('confirmed','Confirmed'),
        ('partialy_paid','Partialy Paid'),
        ('paid', 'Paid'), 
        ('post', 'Post Paid'),
        ('refused','refused')], default='draft',string="Status")
    analytic_id = fields.Many2one('realestate.contract.model', 'Contract')
    
    tax_amount = fields.Integer(string="Tax amount", )

    next_remain = fields.Float('Next Payment Remain Amount')
    saltat_bool = fields.Boolean()
    unit_id = fields.Many2one('real.estate.units', related='analytic_id.unit_id',
        string="Unit", store=True)
    property_id = fields.Many2one('real.estate', related="analytic_id.property_id",
        string="Property", store=True)
    company_id = fields.Many2one('res.company', string="Company", default=lambda self: self.env.user.company_id,
                                 ondelete='restrict')
    renter_id  = fields.Many2one('res.partner',related="analytic_id.partner_id",
        string="Renter", store=True)
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
    
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'rent.contract.payment'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for payment_id in self:
            payment_id.attachment_number = attachment.get(payment_id.id, 0) 

    def return_to_paid(self):
        self.write({
            'state':'paid'
        })

    

    @api.model   
    def create(self, vals):
        vals['name'] = self.env['ir.sequence'].next_by_code('rent.contract.payment') or '/'       
        result = super(AccountAnalyticAccountPayment, self).create(vals)       
        return result

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

