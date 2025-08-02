from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta

class InvestorClearance(models.Model):

    _name = 'investor.clearance'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Investor Clearance'


    name = fields.Char(string="Name" , default=lambda self: _('New'), readonly=True, tracking=True)
    partner_id=fields.Many2one("res.partner", string="Investor" , required=True, domain=[('partner_type','=','investor')], ondelete="cascade", tracking=True)
    contract_id = fields.Many2one('realestate.contract.model', required=True, tracking=True)
    property_id = fields.Many2one(comodel_name='real.estate', string='Property Name', related='contract_id.property_id')
    project_id = fields.Many2one(comodel_name='project.project', string='Project', related='contract_id.property_id.project_id')
    investment_type = fields.Selection(related='contract_id.investment_type', string="Investment Type")
    investor_ratio = fields.Float(string="Investor Ratio", digits=(16, 2), related='contract_id.investor_ratio')
    shares = fields.Integer(string='Number of Shares', related='contract_id.shares')
    investment_amount = fields.Monetary(string='Investment Amount', readonly=True, related='contract_id.investment_amount')
    share_amount= fields.Float(string="Amount/ Percent", related='contract_id.share_amount')
    commission_type= fields.Selection(string="Type", related='contract_id.commission_type')
    is_cleared = fields.Boolean('Clearing Status', related='contract_id.is_cleared')
    clear_type = fields.Selection(related='contract_id.clearance_type', string="Previous Clearance Type")

    date = fields.Date(string=' Date ')
    date_start = fields.Date(string='Start Date ', related='contract_id.date_start')
    date_end = fields.Date(string='End Date', related='contract_id.date_end')
    delivery_date = fields.Date(string='Delivery Date', related='contract_id.delivery_date')
    sign_date = fields.Date(string='Signing date', related='contract_id.sign_date')

    profit = fields.Float(string="Project Profit", tracking=True)
    clearance_amount = fields.Float(string="Clearance Amount", compute='calculate_clearance', store=True, readonly=True, tracking=True)
    trans_amount = fields.Float(string="Transfer Amount", tracking=True)
    shares_num = fields.Float(string="Number of Shares", tracking=True)
    share_profit = fields.Float(string="Earnings per Share Ratio", digits=(16, 2), tracking=True)

    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",default=lambda self: self.env.company.currency_id.id)
    journal_id = fields.Many2one('account.journal', tracking=True, domain="[('type', 'in', ('cash','bank'))]")
    account_id = fields.Many2one('account.account', tracking=True)
    account_analytic_id = fields.Many2one('account.analytic.account', tracking=True)
    move_id = fields.Many2one('account.move', string='Move',readonly=True, tracking=True)
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    trans_property_id = fields.Many2one(comodel_name='real.estate', string='Property Name', tracking=True)
    investor_contract = fields.Many2one('realestate.contract.model', tracking=True)

    note = fields.Char(string="Note", tracking=True)
    description = fields.Char(string="Description", tracking=True)

    clearance_type = fields.Selection([
                                    ('complete', 'Full Clearance'),
                                    ('shares', 'Shares Clearance'),
                                    ('capital', 'Capital Clearance'),
                                    ('profit', 'Profit Clearance'),
                                    ('trans', 'Transfer to Another Project'),],
                                    'Clearance Type', tracking=True)

    state = fields.Selection([('draft', 'Draft'),
                              ('finance', 'Financial approval'),
                              ('investment', 'Investment approval'),
                              ('general', 'General approval'),
                              ('approved', 'Approved'),],
                             'State', readonly=True, default='draft', tracking=True)

    actual_investor_ratio = fields.Float(string="Actual Investor Ratio", compute='_compute_actual_investor_ratio')

    def unlink(self):
        raise exceptions.UserError("Deletion of records is not allowed.")

    @api.depends('contract_id', 'investor_ratio', 'share_amount')
    def _compute_actual_investor_ratio(self):
        for rec in self:
            if rec.share_amount:
                rec.actual_investor_ratio = rec.investor_ratio * rec.share_amount
            else:
                rec.actual_investor_ratio = 1

    @api.depends('clearance_type', 'investment_amount', 'profit', 'share_amount', 'investor_ratio','shares_num','share_profit')
    def calculate_clearance(self):
        for rec in self:
            # investor_profit = rec.profit * rec.share_profit
            investor_profit = rec.profit * rec.investor_ratio
            shares_profit = rec.share_amount * rec.shares_num
            if rec.clearance_type == 'complete':
                rec.clearance_amount = rec.investment_amount + investor_profit
            elif rec.clearance_type == 'shares':
                rec.clearance_amount = shares_profit
            elif rec.clearance_type == 'capital':
                rec.clearance_amount = rec.investment_amount
            elif rec.clearance_type == 'profit':
                rec.clearance_amount = investor_profit
            elif rec.clearance_type == 'trans':
                rec.clearance_amount = 0.0
            else:
                rec.clearance_amount = 0.0

    def create_move(self):
        move_vals = {
            'journal_id': self.journal_id.id,
            # 'move_type': 'in_receipt',
            # 'company_id': self.company_id.id,
            'ref': self.name + "تصفية مستثمر - تحويل لمشروع اخر",
            'date': self.date or fields.Date.today(),
            'line_ids': [(0, 0, {
                'name':  _(self.name),
                'account_id': self.account_id.id,
                'debit': abs(self.trans_amount),
                'partner_id': self.partner_id.id,
                'analytic_account_id':self.account_analytic_id.id,
                'credit': 0,})
            ,(0, 0, {
                'name':_(""),
                'account_id': self.journal_id.default_account_id.id,
                'partner_id': self.partner_id.id,
                'analytic_account_id':self.account_analytic_id.id,
                'debit':0,
                'credit':abs(self.trans_amount)})],
            }

        account_move = self.env['account.move'].create(move_vals)
        self.write({
            'move_id' : account_move,
        })

    def create_contract(self):
        last_contract = self.env['realestate.contract.model'].search([], order='id desc', limit=1)
        if last_contract:
            last_sequence = int(last_contract.name.split('/')[-1])
        else:
            last_sequence = 0
        new_sequence = last_sequence + 1
        new_contract_name = f'CP/{new_sequence:02d}'
        contract = self.env['realestate.contract.model'].create({
                                'state':'draft',
                                'name': new_contract_name,
                                'contract_type':'all_property',
                                'contract_partner_type':'investment',
                                'investment_type':'shares',
                                'is_transfer':True,
                                'transfer_amount':self.trans_amount,
                                'date': self.date,
                                'partner_id': self.partner_id.id,
                                'property_id': self.trans_property_id.id,
                                'investor_clearance_id': self.id,
                            })
        self.investor_contract = contract.id

    @api.model
    def create(self, vals):
        code = 'investor.clearance.code'
        if vals.get('name', 'New') == 'New':
            message = 'IC' + self.env['ir.sequence'].next_by_code(code)
            vals['name'] = message
        return super(InvestorClearance, self).create(vals)

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update the domain of contract_id based on the selected partner.

        """
        if self.partner_id:
            contract_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'confirmed'),
                ('investment_type','=','shares')
            ]
            return {'domain': {'contract_id': contract_domain}}
        else:
            return {'domain': {'contract_id': []}}

    def action_wait_finance(self):
        return self.write({'state': 'finance'})

    def action_wait_investment(self):
        if not self.journal_id:
            raise UserError('Please set the journal for this payment')
        if not self.account_id:
            raise UserError('Please set the account for this payment')
        if self.clearance_type != 'trans':
            if not self.exchange_type_id:
                raise UserError('Please set the exchange type for this payment')

        self.contract_id.write({
                    'line_ids': [(0, 0, {
                        'name': self.name,
                        'clearance_type': self.clearance_type,
                        'date': self.date,
                        'investor_ratio': self.share_profit,
                        'shares': self.shares,
                        'investment_amount': self.investment_amount,
                        'share_amount': self.share_amount,
                        'commission_type': self.commission_type,
                        'profit': self.profit,
                        'clearance_amount': self.clearance_amount,
                        'currency_id': self.currency_id.id,
                        'state': self.state,
                    })]
                })

        if self.clearance_type == 'trans':
            self.create_contract()
            self.create_move()
            self.contract_id.write({'state': 'done', 'clearance_type': 'trans', 'is_cleared': True})
        else:

            payment_id = self.env['cash.order'].create({
                        # 'state': 'general',
                        # 'name': new_cash_order_name,
                        'date': fields.date.today(),
                        'exchange_type_id' : self.exchange_type_id.id,
                        'partner_id': self.partner_id.id,
                        'amount' : self.clearance_amount,
                        'journal_id' : self.journal_id.id,
                        'disc' : self.name + ' ' + 'سند صرف لتصفية مستثمر',
                        'investor_clearance_ids' : self.id,
                        'order_line_ids': [(0, 0, {
                            'description': 'تصفية مستثمر',
                            'account_id': self.account_id.id,
                            'amount': self.clearance_amount,
                            # 'state': 'general',
                        })],
                    })
            payment_id.action_confirm()
            payment_id.action_finance()
            self.move_id = payment_id.move_id.id
            if self.clearance_type == 'complete':
                self.contract_id.write({'state': 'done', 
                                        'clearance_type': 'complete', 
                                        'is_cleared': True})

            if self.clearance_type == 'shares':
                remain = self.shares - self.shares_num
                self.contract_id.write({'clearance_type': 'share', 
                                        'is_cleared': True, 
                                        'shares': remain})

            if self.clearance_type == 'capital':
                self.contract_id.write({'clearance_type': 'capital', 
                                        'is_cleared': True, 
                                        'shares': 0})
            
            if self.clearance_type == 'profit':
                self.contract_id.write({'clearance_type': 'profit', 
                                        'is_cleared': True})
        return self.write({'state': 'investment'})

    def action_wait_general(self):
        return self.write({'state': 'general'})

    def action_approve(self):
        return self.write({'state': 'approved'})

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
            'domain': [('investor_clearance_ids', '=', self.id)],
        }

    def open_contract(self):
        tree_view = self.env.ref('rent_contract.real_estate_contract_tree')
        form_view = self.env.ref('rent_contract.real_estate_contract_form')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Investor Contract',
            'res_model': 'realestate.contract.model',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('investor_clearance_id', '=', self.id)],
        }


    
    