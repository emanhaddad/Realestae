# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from datetime import datetime,timedelta
import operator
import re
from odoo import models, fields, api,_
from odoo.exceptions import ValidationError, AccessError,UserError


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

   
