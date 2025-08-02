from odoo import fields , models,api,tools,_
from datetime import datetime,timedelta
from odoo.exceptions import ValidationError, UserError
# from odoo import amount_to_text


class CustodyCategory(models.Model):
    """ To manage custody category """
    _name = 'custody.category'
    _description = 'custody category'

    name = fields.Char('Name', size=64, required=True)
    max_amount = fields.Float('Maximum Amount')
    company_id = fields.Many2one('res.company', 'Company', required=True, readonly=True,
                                 default=lambda self: self.env['res.company']._company_default_get('custody.category'))
    account_id = fields.Many2one('account.account', tracking=True, domain="[('user_type_id.type', '=', 'liquidity')]")
    analytic_id = fields.Many2one('account.analytic.account', tracking=True)
    journal_id =  fields.Many2one('account.journal', required=True,string='Journal', tracking=True)

class FinanceApprovalRequest(models.Model):
    _name = 'custody.request'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _description = 'Petty Cash Request'
    _order = 'custody_date desc'

    # def default_employee(self):
    #     return self.env.user.name
    custody_clear_id = fields.Many2one('custody.clear.request',string='Reconcile')

    def default_currency(self):
        return self.env.user.company_id.currency_id

    def users_fm(self):
        users_obj = self.env['res.users']
        users = []
        for user in users_obj.search([]):
            if user.has_group("custody_request.group_custody_fm"):
                users.append(user.id)
        return users

    def users_dm(self):
        users_obj = self.env['res.users']
        users = []
        for user in users_obj.search([]):
            if user.has_group("custody_request.group_custody_dm"):
                users.append(user.id)
        return users

    def users_am(self):
        users_obj = self.env['res.users']
        users = []
        for user in users_obj.search([]):
            if user.has_group("custody_request.group_custody_am"):
                users.append(user.id)
        return users

    @api.depends('amount','currency_id')
    def _onchange_amount(self):
        from ..models.money_to_text_ar import amount_to_text_arabic
        if self.amount:
            self.num2wo = amount_to_text_arabic(
                self.amount, self.env.user.company_id.currency_id.name)

    def default_company(self):
        return self.env.user.company_id

    def default_user_analytic(self):
        return self.env.user

    @api.returns('self')
    def _default_employee_get(self):
        return self.env.user

    # def manager_default(self):
    #     return self.env.user.manager_id

    @api.depends('amount', 'currency_id')
    def _onchange_amount(self):

        self.num2wo = self.currency_id.amount_to_text(self.amount) if self.currency_id else ''

    name = fields.Char('Reference',readonly=True,default='New', tracking=True)
    description = fields.Char(string='Description', tracking=True, readonly=True, states={
        'draft': [('readonly', False)]})
    custody_category_id = fields.Many2one('custody.category', 'Category', tracking=True, required=True, readonly=True, states={
        'draft': [('readonly', False)]})

    user_name = fields.Many2one('res.users', string='User name',readonly=True, tracking=True, default=_default_employee_get)
    employee_id = fields.Many2one('hr.employee', string='Employee', tracking=True, required=True, readonly=True, states={
        'draft': [('readonly', False)]})
    check_date = fields.Date('Cheque Date', tracking=True, readonly=True, states={
        'draft': [('readonly', False)]} )
    num2wo = fields.Char(string="Amount in word", compute='_onchange_amount', store=True, tracking=True)
    electronig = fields.Boolean(string='Cheque', copy=False, tracking=True)
    cheque_number = fields.Char('Cheque number', tracking=True)
    # check_count = fields.Integer(compute='_compute_check')
    count_je = fields.Integer(compute='_count_je_compute')
    count_diff = fields.Integer(compute='_count_diff_compute')
    check_term = fields.Selection([('not_followup', 'Not Follow-up'),
                                   ('followup', 'Follow-up')
                                   ],
                                  default='not_followup', invisible=True)
    person = fields.Char(string= 'Ben', track_visibility='onchange')

    bank_template = fields.Many2one(related='journal_id.bank_id')
    # check_id = fields.Many2one('check.followup', string="Check Reference", readonly=True)
    custody_date = fields.Date('Date', default=lambda self: fields.Date.today(),track_visibility='onchange', readonly=True, states={
        'draft': [('readonly', False)]}, tracking=True)
    currency_id = fields.Many2one('res.currency', string='Currency',default=default_currency,required=True, readonly=True, states={
        'draft': [('readonly', False)]}, tracking=True)
    amount = fields.Monetary('Requested Amount',required=True,track_visibility='onchange', readonly=True, states={
        'draft': [('readonly', False)]}, tracking=True)
    paid_amount = fields.Float(compute="_amount_all", tracking=True, digits=(16, 2), string='Cleared Amount', readonly=True)
    residual_amount = fields.Float(compute="_amount_all", tracking=True, digits=(16, 2), string='Remaining Amount', readonly=True)

    sequence = fields.Integer(required=True, default=1,)
    state = fields.Selection([('draft','Draft'),
                              ('dm','Submitted'),
                              ('am','Confirmed'),
                              ('fm','Approved'),
                              ('post','Paid'),
                              ('cleared','Cleared'),
                              ('cancel','Cancel')],default='draft', track_visibility='onchange')
    company_id = fields.Many2one('res.company',string="Company",default=default_company, readonly=True, states={
        'draft': [('readonly', False)]})

    # Accounting Fields
    move_id = fields.Many2one('account.move',string='Request Ref',readonly=True)
    clear_move_id = fields.Many2one('account.move',string='clear Ref',readonly=True)
    payment_move_id = fields.Many2one('account.move',string='payment Ref',readonly=True)
    journal_id = fields.Many2one('account.journal',string='Pay by',domain="[('type','in',['cash','bank'])]", readonly=True, states={
        'draft': [('readonly', False)]}, tracking=True)
    custody_journal_id = fields.Many2one('account.journal',string='Employee Account',domain="[('type','=','general')]", readonly=True, states={
        'draft': [('readonly', False)]}, tracking=True)
    journal_type = fields.Selection(related='journal_id.type')
    account_id = fields.Many2one('account.account',compute='_account_compute',string='Custody account')
    user_id = fields.Many2one('res.users', default=default_user_analytic)
    count_journal_entry = fields.Integer(compute='_compute_je')
    count_payment = fields.Integer(compute='_compute_je')
    attachment = fields.Binary(string='Attachments / المرفقات', readonly=True, states={
        'draft': [('readonly', False)]})
    notes = fields.Text(string='Notes / ملاحظات ', readonly=True, states={
        'draft': [('readonly', False)]}, tracking=True)
    residual_clear_type = fields.Selection([('payment','Payment Resuest'),
                              ('with_custody','With Custody')], string="Clear type", tracking=True, readonly=True, states={
        'done': [('readonly', False)]})
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True, required=True, readonly=True, states={
        'draft': [('readonly', False)]})

    @api.model
    def _access_rights(self):
        return {
            'exchange.type': {
                'read': True,
                'write': False,
                'create': False,
                'unlink': False,
            }
        }

    @api.onchange('employee_id')
    def _onchange_employee(self):
        if self.employee_id :
            pervious_request = self.env['custody.request'].search([('employee_id', '=', self.employee_id.id),('state', 'not in', ['draft','cleared','cancel'])])
            if pervious_request :
                print (self.employee_id,"pervious_request::::::::::",pervious_request)
                raise ValidationError("This employee does not cleared the pervious requests")
        
    @api.depends('amount','state')
    def _amount_all(self):
        """
        Functional field function to finds the value of total paid of enrich.

        @param field_name: list contains name of fields that call this method
        @param arg: extra argument
        @return: dictionary of values
        """
  
        res={}
        for record in self:
            val = 0.0
            for line in record.custody_line_ids:
                val += line.cost
            self.paid_amount = val
            self.residual_amount = record.amount - val
        

    def recall(self):
        self.state = 'draft'

    def _compute_je(self):
        if self.move_id:
            self.count_journal_entry = 1
            self.count_payment = 1
        if self.payment_move_id :
            self.count_journal_entry += 1
            self.count_payment += 1
        if self.clear_move_id :
            self.count_journal_entry += 1
            self.count_payment += 1
        else:
            self.count_journal_entry = 0
            self.count_payment = 0

    # def action_check_view(self):
    #     if self.check_date:
    #         tree_view_out = self.env.ref('check_followup.view_tree_check_followup_out')
    #         form_view_out = self.env.ref('check_followup.view_form_check_followup_out')
    #         return {
    #             'type': 'ir.actions.act_window',
    #             'name': 'View Vendor Checks',
    #             'res_model': 'check.followup',
    #             'view_type': 'form',
    #             'view_mode': 'tree,form',
    #             'views': [(tree_view_out.id, 'tree'), (form_view_out.id, 'form')],
    #             'domain': [('source_document', '=', self.name)],
    #
    #         }
    # # @api.onchange('custody_journal_id')
    # # def get_desc(self):
    # #     self.description = 'Custody for account' + ' ' + str(self.user_name.name)

    # def _compute_check(self):
    #     payment_count = self.env['check.followup'].sudo().search_count([('source_document','=',self.name)])
    #     self.check_count = payment_count

    def _count_je_compute(self):
        for i in self:

            if i.move_id:
                i.count_je = 1
            else:
                i.count_je = 0

    def _count_diff_compute(self):
        for i in self:
            if i.move_id2:
                i.count_diff = 1
            else:
                i.count_diff = 0

    def action_journal_entry(self):

        tree_view = self.env.ref('account.view_move_tree')
        form_view = self.env.ref('account.view_move_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'View Journal Entry',
            'res_model': 'account.move',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('id', 'in', [self.move_id.id,self.clear_move_id.id,self.payment_move_id.id])],

        }
    
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
            'domain': [('custody_request_ids', '=', self.id)],

        }

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
            'domain': [('custody_request_ids', '=', self.id)],

        }

    @api.depends('user_name')
    def _account_compute(self):
        setting_ob = self.env['res.config.settings'].search([],order='id desc', limit=1)
        if setting_ob.petty_account_id:
            self.account_id = setting_ob.petty_account_id
        if not self.company_id.petty_account_id:
            raise ValidationError('Please Insert Petty cash account In Company Configuration')
        else:
            self.account_id = self.company_id.petty_account_id

    analytic_account = fields.Many2one('account.analytic.account',string='Analytic Account')

    def confirm_dm(self):
        if self.amount > self.custody_category_id.max_amount:
            raise ValidationError(_("The requested amount (%s) is more than the maximum amount (%s) allowed in the custody category ")% (self.amount, self.custody_category_id.max_amount))
        if self.amount <= 0:
            raise ValidationError("Please Make Sure Amount Field Grater Than Zero !!")
        if self.env.user.name != self.user_id.name:
            raise ValidationError("Please This Request is not For You")
        if self.electronig==True:
            if not self.check_date and not self.check_number:
                raise ValidationError(_('Please enter cheque date and number'))
        user_fm_ids = self.env['res.users'].sudo().search([('id', 'in', self.users_dm())])
        channel_group_obj = self.env['mail.mail']
        partner_list = []
        for rec in user_fm_ids:
            partner_list.append(rec.partner_id.id)
        receipt_ids = self.env['res.partner'].sudo().search([('id','in',partner_list)])
        dic = {
            'subject': _('Cash Request Need Approval: %s') % (self.name,),
            'email_from': self.user_name.login,
            'body_html': 'Hello, Please approve petty cash Request with number ' + self.name,
            'recipient_ids': receipt_ids.ids,
        }
        mail = channel_group_obj.sudo().create(dic)
        mail.send()
        self.write({'state': 'dm'})
        # desc=self.account_id.id
        # self.description= 'Custody for account' + ' ' + str(self.user_name.name)

    def confirm_am(self):
        user_fm_ids = self.env['res.users'].sudo().search([('id', 'in', self.users_am())])
        channel_group_obj = self.env['mail.mail']
        partner_list = []
        for rec in user_fm_ids:
            partner_list.append(rec.partner_id.id)
        receipt_ids = self.env['res.partner'].sudo().search([('id', 'in', partner_list)])
        dic = {
            'subject': _('Cash Request Need Approval: %s') % (self.name,),
            'email_from': self.user_name.login,
            'body_html': 'Hello, Please approve petty cash Request with number ' + self.name,
            'recipient_ids': receipt_ids.ids,
        }
        mail = channel_group_obj.sudo().create(dic)
        mail.send()
        self.write({'state': 'am'})

    def confirm_fm(self):
        user_fm_ids = self.env['res.users'].sudo().search([('id', 'in', self.users_fm())])
        channel_group_obj = self.env['mail.mail']
        partner_list = []
        for rec in user_fm_ids:
            partner_list.append(rec.partner_id.id)
        receipt_ids = self.env['res.partner'].sudo().search([('id', 'in', partner_list)])
        dic = {
            'subject': _('Cash Request Need Approval: %s') % (self.name,),
            'email_from': self.user_name.login,
            'body_html': 'Hello, Please approve petty cash Request with number ' + self.name,
            'recipient_ids': receipt_ids.ids,
        }
        mail = channel_group_obj.sudo().create(dic)
        mail.send()
        self.write({'state': 'fm'})

    @api.model
    def get_amount(self):
        if self.currency_id != self.env.user.company_id.currency_id:
            return self.amount * self.env.user.company_id.currency_id.rate
        if self.currency_id == self.env.user.company_id.currency_id:
            return self.amount

    @api.model
    def get_currency(self):
        if self.currency_id != self.env.user.company_id.currency_id:
            return self.currency_id.id
        else:
            return self.currency_id.id

    @api.model
    def amount_currency_debit(self):
        if self.currency_id != self.env.user.company_id.currency_id:
            return self.amount
        else:
            return self.amount

    @api.model
    def amount_currency_credit(self):
        if self.currency_id != self.env.user.company_id.currency_id:
            return self.amount * -1
        else:
            return self.amount * -1

    # confirm Finance Approval (Posted)
    def confirm_post(self):
        global check_obj, check_val
        account_move_object = self.env['account.move']
        if not self.custody_category_id.journal_id:
            raise ValidationError("Please Make Sure Custody Accounting & Journal Inforamtion was Entered !!")
        if not self.employee_id.address_home_id.id:
            raise UserError(_ ("Please enter employee (%s) home address") % (self.employee_id.name))

        if self.account_id and self.custody_category_id.journal_id :
            l = []
            if not self.custody_category_id.journal_id:
                raise ValidationError("Please Fill Accounting Information in Custody Category!!")
            # if self.check_term != 'followup':
            debit_val = {
                'move_id': self.move_id.id,
                'name': 'Custody for account' + ' ' + str(self.employee_id.name),
                'account_id': self.custody_category_id.account_id.id,
                'debit': self.get_amount(),
                'analytic_account_id' : self.custody_category_id.analytic_id.id,
                'currency_id': self.get_currency() or False,
                'partner_id': self.employee_id.address_home_id.id,
                'amount_currency': self.amount_currency_debit() or False,
                # 'company_id': self.company_id.id,

            }
            l.append((0, 0, debit_val))
            credit_val = {

                'name': 'Custody for account' + ' ' + str(self.employee_id.name),
                'account_id': self.custody_category_id.journal_id.default_account_id.id,
                'credit': self.get_amount(),
                'currency_id': self.get_currency() or False,
                'partner_id': self.employee_id.address_home_id.id,
                'amount_currency': self.amount_currency_credit() or False,
                # 'analytic_account_id': ,
                # 'company_id': ,

            }
            l.append((0, 0, credit_val))
            print("List", l)
            vals = {
                'journal_id': self.custody_category_id.journal_id.id,
                'date': self.custody_date,
                'ref': self.name,
                'partner_id': self.employee_id.address_home_id.id,
                # 'company_id': ,
                'line_ids': l,
            }
            # self.move_id = account_move_object.create(vals)

            payment_id = self.env['cash.order'].create({
                    # 'state': 'general',
                    # 'name': new_cash_order_name,
                    'date': self.custody_date,
                    'exchange_type_id' : self.exchange_type_id.id,
                    'partner_id': self.employee_id.address_home_id.id,
                    'amount' : self.amount,
                    'journal_id' : self.custody_category_id.journal_id.id,
                    'disc' : self.name + 'سند العهده ' + '\n' + 'البيان ' + self.notes,
                    'custody_request_ids' : self.id,
                    'order_line_ids': [(0, 0, {
                        'description': 'أمر صرف لعهده',
                        'account_id': self.custody_category_id.account_id.id,
                        'amount': self.amount,
                        # 'state': 'general',
                    })],
                })

            payment_id.action_confirm()            
            payment_id.action_finance()            
            self.move_id = payment_id.move_id.id

            self.state = 'done'

    @api.model
    def create(self, vals):
        code = 'custody.request.code'
        if vals.get('name', 'New') == 'New':
            message = 'CIM' + self.env['ir.sequence'].next_by_code(code)
            vals['name'] = message
            # self.message_post(subject='Create CR', body='This is New CR Number' + str(message))
        return super(FinanceApprovalRequest, self).create(vals)

    # @api.multi
    def unlink(self):
        for i in self:
            if i.state != 'draft':
                raise ValidationError("Please Make Sure State in DRAFT !!")
            else:
                super(FinanceApprovalRequest, i).unlink()

    def copy(self):
        raise ValidationError("Can not Duplicate a Record !!")

    def cancel_request(self):
        self.state = 'draft'

    def reject(self):
        self.state = 'cancel'

    def clear_custody(self) :
        if not self.custody_line_ids :
            raise ValidationError(_('Please enter statements'))

        if not self.employee_id.address_home_id:
            raise ValidationError(_('Please enter home address for the employee'))

        lines = []
        credit_amount = sum(line.cost for line in self.custody_line_ids)
        payment_id = False

        if not self.clear_move_id :
            for line_id in self.custody_line_ids:
                debit_line_vals = {
                    'debit': line_id.cost,
                    'credit': 0.0,
                    'account_id': line_id.statement_id.account_id.id,
                    'analytic_account_id': self.custody_category_id.analytic_id.id,
                    'currency_id': self.get_currency() or False,
                    'partner_id': line_id.custody_request_id.employee_id.address_home_id.id,
                    'amount_currency': self.amount_currency_debit() or False,
                    'name': self.notes,
                    }
                lines.append((0, 0, debit_line_vals))

            credit_line_vals = {
                'debit': 0.0,
                'credit': credit_amount,
                'name': self.notes,
                'partner_id': self.employee_id.address_home_id.id,
                'account_id': self.custody_category_id.account_id.id,
                }
            lines.append((0, 0, credit_line_vals))

            clearance_move = self.env['account.move'].create({
                'company_id': self.company_id.id,
                'journal_id': self.custody_category_id.journal_id.id,
                'date': fields.Date.today(),
                'ref': self.name,
                'order_id': False,
                'line_ids': lines,
                })
        self.clear_move_id = clearance_move

        if not self.attachment :
            raise ValidationError(_('Please upload the attachment for this clearance'))

        if self.residual_amount > 0 and not self.residual_clear_type :
            raise ValidationError(_('Please specify the clearance type (receive payment - create new custody with the residual amount)'))

        if self.residual_amount > 0 and self.residual_clear_type == 'payment':
            payment_id = self.env['cash.receive'].create({
                    # 'state': 'general',
                    # 'name': new_cash_receive_name,
                    'date': self.custody_date,
                    'partner_id': self.employee_id.address_home_id.id,
                    'amount': self.residual_amount,
                    'journal_id' : self.custody_category_id.journal_id.id,
                    'disc' : self.name + 'سند العهده ',
                    'custody_request_ids' : self.id,
                    'order_line_ids': [(0, 0, {
                        'description': 'سند قبض لمتقي عهده',
                        'account_id': self.custody_category_id.account_id.id,
                        'amount': self.residual_amount,
                        # 'state': 'general',
                    })],
                })

            payment_id.action_confirm()
            payment_id.action_finance()
            self.payment_move_id = payment_id.move_id.id

        elif self.residual_amount < 0 :
            payment_id = self.env['cash.order'].create({
                    # 'state': 'general',
                    # 'name': new_cash_order_name,
                    'date': self.custody_date,
                    'exchange_type_id' : self.exchange_type_id.id,
                    'partner_id': self.employee_id.address_home_id.id,
                    'amount': abs(self.residual_amount),
                    'journal_id' : self.custody_category_id.journal_id.id,
                    'disc' : self.name + 'سند العهده',
                    'custody_request_ids' : self.id,
                    'order_line_ids': [(0, 0, {
                        'description': 'سند صرف لعهده',
                        'account_id': self.custody_category_id.account_id.id,
                        'amount': abs(self.residual_amount),
                        # 'state': 'general',
                    })],
                })

            payment_id.action_confirm()
            payment_id.action_finance()

            self.payment_move_id = payment_id.move_id.id

        if self.residual_amount > 0 and self.residual_clear_type == 'with_custody':
            custody_request_id = self.env['custody.request'].create({
                    'employee_id' : self.employee_id.id,
                    'exchange_type_id' : self.exchange_type_id.id,
                    'custody_category_id' : self.custody_category_id.id,
                    'notes' : 'تصفية متبقي عهدة سابفة',
                    'amount' : self.residual_amount,
                })
            return self.write({'state': 'cleared'})

        # self.clear_move_id = payment_id.move_id.id

        self.state = 'cleared'


    ###################################################

class InheritCompany(models.Model):
    _inherit = 'res.company'

    petty_account_id = fields.Many2one('account.account',string='Petty cash account')
