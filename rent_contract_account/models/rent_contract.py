import re
from odoo import models, fields, api ,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, AccessError,UserError
from odoo.tools.translate import _

class RealEstateContract(models.Model):
    _inherit = 'realestate.contract.model'

    def calculate_contract_payments(self):
        for rec in self:
            rec.paid_amount = sum(rec.payment_ids.filtered(lambda x: x.rental_fees == False).mapped('paid_amount'))
            rec.residual_amount = sum(rec.payment_ids.filtered(lambda x: x.rental_fees == False).mapped('pay_amount')) - rec.paid_amount

    contract_account_type = fields.Selection([('invoice','Invoice & payment'),('payment','payment only')], string='Accounting type',required=False, tracking=True)
    account_payment_ids = fields.Many2many('account.payment', string='Payments',required=False)
    invoice_ids = fields.Many2many('account.move', string='Payments',required=False)
    paid_amount = fields.Monetary(string='Paid Amount',compute='calculate_contract_payments')
    residual_amount = fields.Monetary(string='Residual Amount', compute='calculate_contract_payments')

    
            

    def action_payments(self):
        domain = [('id', 'in',self.account_payment_ids.ids)]
        return {
          'name': _('Attachments'),           
          'domain': domain,          
          'res_model': 'account.payment', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form,kanban',
          'view_type': 'form',
          }


    def action_invoices(self):
        domain = [('id', 'in',self.invoice_ids.ids)]
        return {
          'name': _('Invoices'),           
          'domain': domain,          
          'res_model': 'account.move', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form,kanban',
          'view_type': 'form',
          }



class AccountAnalyticAccountPayment(models.Model):
    _inherit = "rent.contract.payment"

   
    move_id = fields.Many2one('account.move', string='Move',required=False)
    payment = fields.Many2one('account.payment')
    invoice = fields.Many2one('account.move')
    rental_fees = fields.Boolean()

    def create_move(self):
        move_vals = {
            'journal_id': self.journal_id.id,
            # 'move_type': 'in_receipt',
            'company_id': self.company_id.id,
            'ref': self.analytic_id.contract_no + "للعقد رقم " + ' ' + self.name + "دفعية رقم ",
            'date': self.pay_date or fields.Date.today(),
            'line_ids': [(0, 0, {
                'name':  _(self.name),
                'account_id': self.account_id.id,
                'debit': 0,
                'partner_id': self.renter_id.id,
                'analytic_account_id':self.account_analytic_id.id,
                'credit': abs(self.paid_amount),})
            ,(0, 0, {
                'name':  _(self.name),
                'account_id': self.journal_id.default_account_id.id,
                'partner_id': self.renter_id.id,
                'debit':abs(self.paid_amount),
                'credit':0})],
            }

        account_move = self.env['account.move'].create(move_vals)
        self.write({
            'move_id' : account_move,
        })

    def action_review(self):
        for record in self:
            if record.name == '/':
                # Fetch the last sequence number across all records
                last_payment = self.search([('name', '!=', '/')], order='id desc', limit=1)
                if last_payment:
                    last_sequence = last_payment.name
                    match = re.search(r'\d+$', last_sequence)
                    if match:
                        last_sequence_number = int(match.group())
                    else:
                        last_sequence_number = 0
                else:
                    last_sequence_number = 0

                # Generate new sequence number
                new_sequence_number = last_sequence_number + 1
                new_sequence = f'PAY{new_sequence_number:03d}'
                record.name = new_sequence
            record.write({
                'state': 'review',
            })


    def action_confirm(self):
        if not self.journal_id:
            raise UserError("Please selecte the journal")
        if not self.account_id:
            raise UserError("Please selecte the account")

        self.create_move()
        # self.create_invoice_payment(self.env.user.company_id.income_journal_id)
        if self.paid_amount > self.pay_amount:
            raise ValidationError('Paid amount can not be greater than payment amount')

        if self.paid_amount < self.pay_amount:
            self.env['rent.contract.payment'].create({
                'rental_fees':True,
                'pay_amount': self.pay_amount - self.paid_amount,
                'pay_date':self.pay_date,
                'renter_id':self.renter_id.id,
                'analytic_id': self.analytic_id.id,
                #'property_id':self.property_id.id
                })
            return self.write({'state': 'partialy_paid'})
        
        return self.write({'state': 'paid'})

    def create_invoice_payment(self, journal):
        payment_id = self.env['rent.contract.payment'].search([('id','=',self._context.get('active_id', False))])
        # income journal 
        #journal_id = self.env.user.company_id.income_journal_id
        #print("journal_id--------------------------",journal_id)

        # preparing voucher line description
        name = _("Property : ") + str(payment_id.property_id.name) + \
                            ' ' + str(payment_id.property_id.code)
        name += _(" / Check Number : ") + str(self.check_number) if self.payment_type == 'check' else ''
        name += _(" / Due Date : ") + str(self.due_date)
        account_id = self.property_id.income_account_id.id 
        if self.unit_id:
            analytic_id = self.unit_id.analytic_id if self.unit_id.analytic_id \
            else self.property_id.analytic_id


            #account_id = self.unit_id.income_account_id if self.unit_id.income_account_id \
            #else self.property_id.income_account_id
            #account_id = self.env.user.company_id.account_id if not account_id else account_id

        else:
            analytic_id = self.property_id.analytic_id

            #account_id = self.property_id.income_account_id if self.property_id.income_account_id \
            #else self.env.user.company_id.account_id

        if not journal:
            raise ValidationError(_("Sorry !! can you please configuer Income Journal"))
        if not analytic_id:
            raise ValidationError(_("Sorry !! can you please configuer Income Analytic"))
        if not account_id:
            raise ValidationError(_("Sorry !! can you please configuer Income Accont"))



        print("account_id-----------------------",account_id)

      
        print("analytic_id------------------------",analytic_id)
        partner_id = self.renter_id.id
        '''
        move_line_1={
                'name': _("Income of %s", self.property_id.name),
                'account_id': journal.default_account_id.id,
                'debit': abs(self.paid_amount),
                'analytic_account_id':analytic_id.id,
                'credit': 0,
                #'display_type':'line_note'
            }
        move_line_2={
                'name':_(""),
                'account_id':  account_id.id,
                'debit':0,
                'credit':abs(self.paid_amount)}

        move_vals = {
            'journal_id': journal.id,
            'move_type': 'entry',
            'partner_id' :partner_id,
            'ref': _("Income of %s", self.property_id.name),
            'date': fields.Date.today(),
            'line_ids': [(0, 0,move_line_1)
            ,(0, 0,move_line_2)],
            }
        '''
        if self.analytic_id.contract_account_type == 'invoice' and not self.rental_fees:
            invoice_line={
                    'name': _("Income of %s", self.name + ' ' + self.property_id.name + '/' + self.unit_id.code),
                    'account_id': account_id.id,
                    'price_unit': self.pay_amount,
                    'analytic_account_id':analytic_id.id,
                    'quantity':1,
                    #'credit': 0,
                    #'display_type':'line_note'
                }
            

            move_vals = {
                'journal_id': self.env.user.company_id.income_journal_id.id,
                'move_type': 'out_invoice',
                'partner_id' :partner_id,
                'ref': _("Income of %s", self.property_id.name),
                'date': fields.Date.today(),
                'invoice_line_ids': [(0, 0,invoice_line)
                ],
                }
            invoice = self.env['account.move'].create(move_vals)
            #account_move._post()
            self.analytic_id.invoice_ids = [(4,invoice.id)]
            self.invoice = invoice.id
        elif self.analytic_id.contract_account_type == 'payment' and not self.rental_fees:
            cash_bank_journal=self.env['account.journal'].search([('type','in',('cash','bank'))],limit=1)
            payment = self.env['account.payment'].sudo().create({
            'partner_id':partner_id,
            'journal_id':cash_bank_journal[0].id,
            'destination_account_id':self.env.user.company_id.account_id.id,
            'cost_center':self.property_id.analytic_id.id,
            'ref':self.name + "\n" + self.analytic_id.name,
            'payment_type':'inbound',
            'amount':self.pay_amount,})
            self.analytic_id.account_payment_ids = [(4,payment.id)]
            self.payment = payment.id

        elif self.rental_fees:
            cash_bank_journal=self.env['account.journal'].search([('type','in',('cash','bank'))],limit=1)
            payment = self.env['account.payment'].sudo().create({
            'partner_id':partner_id,
            'journal_id':cash_bank_journal[0].id,
            'ref':self.name + "\n" + self.analytic_id.name,
            'payment_type':'outbound',
            'amount':self.pay_amount,})
            self.analytic_id.account_payment_ids = [(4,payment.id)]
            self.payment = payment.id
        
class payment_confirmation_wiz(models.TransientModel):
    _inherit= 'payemnt.confirmation.wiz'


    

    def confirm_payment(self):
        print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        income_journal_id = self.env['res.company'].search([]).income_journal_id
        print("<<<<<<<<<<<<<<<<<<",income_journal_id)
        if not income_journal_id:
            raise ValidationError(_("Set Journal in settings"))

        payment_id =self._context.get('active_id', False)
        payment_id = self.env['rent.contract.payment'].browse(payment_id)
        if payment_id.analytic_id.state not in ['confirmed','hanging']:
            raise ValidationError(_("contract of this payment is not valid"))
        else:
            payment_id.pay_date = fields.date.today()
            if round(self.amount,2) > round(payment_id.pay_amount , 2):
                raise ValidationError(_("Payment amount is more than contract amount"))
            elif self.amount <= 0.0 :
                raise ValidationError(_("Payment amount is must be more than zero"))
            elif round(self.amount,2) < round(payment_id.pay_amount , 2):
                self.env['rent.contract.payment'].create({
                    'name':payment_id.name +"/1",
                    'property_id':payment_id.property_id.id,
                    'unit_id':payment_id.unit_id.id,
                    'supervisor_id':payment_id.supervisor_id.id,
                    'renter_id':payment_id.renter_id.id,
                    'analytic_id':payment_id.analytic_id.id,
                    'due_date':payment_id.due_date,
                    'pay_amount':round(payment_id.pay_amount,2) - round(self.amount,2) ,
                    'payment_id':payment_id.id,
                    'state':'draft',
                })
                payment_id.write({
                    'paid_amount' : round(self.amount,2),
                    'state' : 'partialy_paid',
                    #'journal_id':self.journal_id.id,
                    'payment_state':self.payment_state,
                    'payment_type':self.payment_type,
                    'check_number':self.check_number,
                    'note':self.note,
                    'pay_date':self.payemnt_date,
                })
            elif round(self.amount,2) == round(payment_id.pay_amount,2):
                self.close_parent_payments(payment_id)
                payment_id.write({
                    'state' : 'paid',
                    'paid_amount' : self.amount,
                    # 'journal_id' : self.journal_id.id,
                    'payment_state':self.payment_state,
                    'payment_type':self.payment_type,
                    'check_number':self.check_number,
                    'note':self.note,
                    'pay_date':self.payemnt_date,
                })
            
        if payment_id.analytic_id :
            self.check_contract(payment_id.analytic_id)
        



    
class AccountPayment(models.Model):
    _inherit= 'account.payment'    


    def action_post(self):
        for rec in self:
            super(AccountPayment, self).action_post()
            contract_payment=self.env['rent.contract.payment'].search([('payment','=',rec.id)])
            if contract_payment and not contract_payment.rental_fees:
                contract_payment.paid_amount = rec.amount
            elif contract_payment and contract_payment.rental_fees:
                contract_payment.paid_amount = -1* rec.amount

    def action_draft(self):
        for rec in self:
            super(AccountPayment, self).action_draft()
            contract_payment=self.env['rent.contract.payment'].search([('payment','=',rec.id)])
            if contract_payment:
                contract_payment.paid_amount = 0

