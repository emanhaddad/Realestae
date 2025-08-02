import re
from odoo import api, fields, models, _
from . import amount_to_text as amount_to_text_ar
from odoo.exceptions import UserError, ValidationError

class cash_order(models.Model):
    _name = "cash.receive"
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'sequence.mixin']
    _description = 'Cash Receive'
    _rec_name='name'

    
    def unlink(self):
        raise exceptions.UserError("Deletion of records is not allowed.")

    def action_confirm(self):
        for order in self:
            if order.state != 'general':
                order.write({
                    'name': self.env['ir.sequence'].sudo().next_by_code('cash.receive') or '/',
                    'state': 'general',
                })
                for line in order.order_line_ids:
                    line.state = 'general'

    def action_refuse_confirm(self):
        self.state = 'draft'
        for line in self.order_line_ids:
            line.state = 'draft'

    def action_general(self):
        self.state = 'general'
        for line in self.order_line_ids:
            line.state = 'general'

    def action_refuse_general(self):
        self.state = 'draft'
        for line in self.order_line_ids:
            line.state = 'draft'

    def action_finance(self):
        scheduled_amount = sum(line.amount for line in self.order_line_ids)
        if scheduled_amount != self.amount:
            raise UserError(
                _('Please make suer that schedule amount is equal to total amount  ^_^'))

        if self.move_id:
            self.move_id.unlink()
        
        move_id = self.create_move()
        self.move_id = move_id
        self.state = 'financial'
        for line in self.order_line_ids:
                line.state = 'financial'

    def action_refuse_finance(self):
        scheduled_amount = sum(line.amount for line in self.order_line_ids)
        if scheduled_amount != self.amount:
            raise UserError(
                _('Please make suer that schedule amount is equal to total amount  ^_^'))
        else:
            self.state = 'general'
            for line in self.order_line_ids:
                line.state = 'general'

    @api.depends('amount')
    def compute_amount(self):
        self.amount_in_word = amount_to_text_ar.amount_to_text(
            self.amount, 'ar')
    
    def create_move(self):
        line_ids = []
        journal_ids = {}

        # creating debit lines for expensess and grouping payment 
        # depending on journals 
        for line_id in self.order_line_ids:
            if line_id.journal_id in journal_ids.keys():
                journal_ids[line_id.journal_id.id]['amount'] += line_id.amount 
            else : 
                journal_ids[line_id.journal_id.id] = {
                    'journal_id':line_id.journal_id,
                    'amount' : line_id.amount,
                }
            line_ids.append((0, 0, {
                'debit': 0.0,
                'credit': line_id.amount, 
                'partner_id': self.partner_id.id,
                'account_id': line_id.account_id.id,
                'name': self.disc,
                'analytic_account_id' : line_id.analytic_account_id.id,
            }))
        
        # creating credit lines from goruped lines 
        for key in journal_ids.keys():
            if not journal_ids[key]['journal_id'].default_account_id:
                raise UserError(_('Can you please add default account for journal %s ', self.journal_id.name))
            
        line_ids.append((0, 0, {
                'debit': self.amount,
                'credit': 0.0, 
                'partner_id': self.partner_id.id,
                'name': self.disc,
                'account_id': self.journal_id.default_account_id.id,

            }))

        move_id = self.env['account.move'].create({
            'company_id': self.company_id.id,
            'journal_id': self.journal_id.id,
            'date': fields.date.today(),
            'ref': self.name,
            # 'order_id': self.id,
            'line_ids': line_ids,
        })

        #move_id.post()
        return move_id

    def action_pay(self):
        total = sum(line.amount for line in self.order_line_ids)
        if int(self.amount) != int(total):
            raise UserError(
                _('invalid amount \n pleas check that the amount is equals to liens amount  ^_^'+str(self.amount)+'  '+str(total)))
        # move_id = self.create_move()
        self.move_id.action_post()
        self.write({
            #'move_id' : move_id.id,
            'state' : 'paid',
        })
                
    company_id = fields.Many2one('res.company', 'Company',  readonly=True, states={
        'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)
    employee_id = fields.Many2one("hr.employee", tracking=True, string='Employee', readonly=True,traking=3 )
    
    partner_id = fields.Many2one(
        "res.partner", string="Recipient from", required=True, track_visibility='onchange', readonly=True, states={
        'draft': [('readonly', False)]})
    department_id = fields.Many2one(
        "hr.department", string="Department", readonly=True)
    project_id = fields.Many2one('project.project', 'Project', tracking=True, readonly=True, states={
        'draft': [('readonly', False)]})
    projects = fields.Many2many('project.project', string="Projects", tracking=True)

    amount = fields.Float('Amount by Numbers', required=True, track_visibility='onchange')
    amount_in_word = fields.Char(
        compute="compute_amount", store=True, string="Amount in Text", readonly=True)
    disc = fields.Text(string="Description", required=True, readonly=True, states={
        'draft': [('readonly', False)]}, tracking=True)
    name = fields.Char(string="Sequence", default="/")
    recipient_name = fields.Char(string="Recipient Name", track_visibility='onchange', readonly=True, states={
        'draft': [('readonly', False)]})
    date = fields.Date("Date", default=fields.Date.today(), track_visibility='onchange', readonly=True, states={
        'draft': [('readonly', False)]})
    state = fields.Selection([
        ('draft', 'Draft'),
        ('general', 'Accountant'),
        ('financial', 'Waiting for Finacial Manager'),
        ('paid', 'Paid'), ('refuse', 'Refused')
    ], "State", default="draft", track_visibility='onchange')
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        tracking=True
    )

    move_id = fields.Many2one(
        string="Account Move",
        comodel_name="account.move",
        store=True,
        readonly=True,
    )

    order_line_ids = fields.One2many(
        string="Expensess Lines",
        comodel_name="cash.receive.line",
        inverse_name="order_id",
    )
    rejection_reason = fields.Text()

    custody_request_ids = fields.Many2one(
        'custody.request',
        string="Custody Request",
        readonly=True,
        copy=False,
        tracking=True
    )

    booking_request_ids = fields.Many2one(
        'real.estate.booking',
        string="Booking Request",
        readonly=True,
        copy=False,
        tracking=True
    )
    investment_request_ids = fields.Many2one(
        'realestate.contract.model',
        string="Investment Request",
        readonly=True,
        copy=False,
        tracking=True
    )
    delegate_request_ids = fields.Many2one(
        'real.estate.delegate',
        string="Delegate Request",
        readonly=True,
        copy=False,
        tracking=True
    )

    check_number = fields.Char(string="Check number", tracking=True)

    def unlink(self):
        for order in self :
            if order.state != 'draft':
                raise UserError(_('You cannot perform this action on cash order not on state draft.'))
        return super(cash_order, self).unlink()

    @api.model
    def create(self, vals):
        employee_id = self.env['hr.employee'].search([('user_id', '=', self.env.user.id)], limit=1)
        if not employee_id:
            raise UserError(_('Current user has no related employee'))
        vals ['employee_id'] = employee_id.id,
        vals['department_id'] = employee_id.department_id.id
        result = super(cash_order, self).create(vals)
        return result

class cash_order_line(models.Model):
    _name = 'cash.receive.line'
    _description = 'Payment Details'

    amount = fields.Float(string="Amount", required=True,)
    order_id = fields.Many2one(
        string="Order",
        comodel_name="cash.receive",
    )
    journal_id = fields.Many2one(
        string="Journal",
        comodel_name="account.journal",
        related="order_id.journal_id",
        store=True,
        tracking=True
    )

    analytic_account_id = fields.Many2one(
        'account.analytic.account', string="Analytic Account")

    company_id = fields.Many2one('res.company' , default=lambda self: self.env.user.company_id)

    account_id = fields.Many2one("account.account", string="Account" , domain="[('company_id' , '=' ,company_id)]")
    description = fields.Text(string="Description",)
    state = fields.Selection(
        string="State",
        selection=[
            ('draft', 'Draft'),  
            ('general', 'Waiting for Finacial Manager'),
            ('financial', 'waiting for Auditor'),
            ('paid', 'Paid'), ('refuse', 'Refused')
    ],related="order_id.state", tracking=True)
