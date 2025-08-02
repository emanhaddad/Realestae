from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError
from dateutil.relativedelta import relativedelta

class ProfitsCount(models.Model):

    _name = 'profits.count'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Profits Count'


    name = fields.Char(string="Name" , default=lambda self: _('New'), readonly=True)
    date = fields.Date(string="Date", track_visibility='onchange')
    property_id = fields.Many2one(comodel_name='real.estate', string='Property Name', required=True, track_visibility='onchange')
    project_id = fields.Many2one(comodel_name='project.project', string='Project', related='property_id.project_id')
    property_share_number = fields.Integer(string="Number of Shares" , related='property_id.property_share_number')
    construction_cost = fields.Float(string="Total Construction Cost", digits=(16, 2), track_visibility='onchange')
    admin_expens = fields.Float(string="Administrative Expenses", digits=(16, 2), track_visibility='onchange')
    market_expens = fields.Float(string="Marketing Expenses", digits=(16, 2), track_visibility='onchange')
    expense = fields.Float(string="Total Expense", digits=(16, 2), compute='_compute_total_expense', readonly=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency")
    note = fields.Char(string="Notes", tracking=True)
    property_cost = fields.Float(string="Total Property Cost", digits=(16, 2), track_visibility='onchange')
    income = fields.Float(string="Total Income", digits=(16, 2), track_visibility='onchange')
    profit = fields.Float(string="Total Profit", digits=(16, 2), compute='_compute_total_profit', readonly=True)
    profit_ratio = fields.Float(string="Profit Ratio", digits=(16, 2), compute='_compute_total_profit')
    company_ratio = fields.Float(string="Company Ratio", digits=(16, 2), track_visibility='onchange')
    company_profit = fields.Float(string="Company Profit", digits=(16, 2), compute='_compute_share_profit')
    share_value = fields.Float(string="Share Value", digits=(16, 2), compute='_compute_share_profit')
    share_profit = fields.Float(string="Earnings per Share Ratio", digits=(16, 2), compute='_compute_share_profit')

    state = fields.Selection([('draft', 'Draft'),
                              ('review', 'Review'),
                              ('done', 'Done'),],
                             'State', readonly=True, default='draft', track_visibility='onchange')
    line_ids = fields.One2many('profits.count.line', 'line_id')  

    move_id = fields.Many2one('account.move', string='Move', tracking=True)
    journal_id = fields.Many2one('account.journal', string='Journal', tracking=True)
    account_id = fields.Many2one('account.account', string='Account', tracking=True)
    account_analytic_id = fields.Many2one('account.analytic.account', string='Cost Center', tracking=True)

    profit_move_id = fields.Many2one('account.move', string='Profit Move', tracking=True)
    profit_journal_id = fields.Many2one('account.journal', string='Profit Journal', tracking=True)
    profit_account_id = fields.Many2one('account.account', string='Profit Account', tracking=True)
    profit_account_analytic_id = fields.Many2one('account.analytic.account', string='Profit Cost Center', tracking=True)
    company_id = fields.Many2one('res.company', 'Company',  readonly=True, states={
        'draft': [('readonly', False)]}, default=lambda self: self.env.user.company_id)  

    def action_review(self):
        return self.write({'state': 'review'})

    def action_done(self):
        self.create_expense_move()
        # self.create_profit_move()
        self.transfer_selected_lines_to_real_estate()
        if self.share_value > 0:
            self.update_property_profit()
        return self.write({'state': 'done'})

    def unlink(self):
        raise UserError("Deletion of records is not allowed.")


    @api.model
    def create(self, vals):
        code = 'profits.count.code'
        if vals.get('name', 'New') == 'New':
            message = 'PC' + self.env['ir.sequence'].next_by_code(code)
            vals['name'] = message
        return super(ProfitsCount, self).create(vals)

    @api.onchange('property_id')
    def _onchange_property_id(self):
        if self.property_id:
            self.update_line_ids()

    def update_line_ids(self):
        if self.property_id:
            units = self.env['real.estate.units'].search([
                ('base_property_id', '=', self.property_id.id)
                # ('profit_calculated', '=', False)
            ])
            line_ids = [(5, 0, 0)]  # Clear existing lines
            for unit in units:
                line_ids.append((0, 0, {'unit_id': unit.id}))
            self.line_ids = line_ids

    @api.depends('construction_cost', 'admin_expens', 'market_expens')
    def _compute_total_expense(self):
        for rec in self:
            rec.expense = rec.construction_cost + rec.admin_expens + rec.market_expens


    @api.depends('property_cost', 'income')
    def _compute_total_profit(self):
        for rec in self:
            rec.profit = rec.income - rec.property_cost
            if rec.property_cost != 0:
                rec.profit_ratio = (rec.profit / rec.property_cost)
            else:
                rec.profit_ratio = 0 


    @api.depends('profit_ratio', 'company_ratio')
    def _compute_share_profit(self):
        for rec in self:
            if rec.company_ratio > 0:
                rec.company_profit = rec.profit * rec.company_ratio
            else:
                rec.company_ratio = 0
            net_profit = rec.profit - rec.company_profit
            if rec.property_share_number > 0 and net_profit > 0:
                rec.share_value = net_profit / rec.property_share_number
                rec.share_profit = rec.share_value / net_profit
            else:
                rec.share_value = 0
                rec.share_profit = 0

    def transfer_selected_lines_to_real_estate(self):
        for line in self.line_ids:
            if line.calculate_profit:
                self.property_id.write({
                    'unit_profit_ids': [(0, 0, {
                        'unit_id': line.unit_id.id,
                        'property_type_id': line.property_type_id.id,
                        'unit_space': line.unit_space,
                        'unit_amount': line.unit_amount,
                        'space': line.space,
                        'unit_cost': line.unit_cost,
                        'amount': line.amount,
                    })]
                })
                line.unit_id.write({'profit_calculated': True})
    '''

    def update_property_profit(self):
        for rec in self:
            rec.property_id.write({
                'property_line_ids': [(0, 0, {
                    'date': rec.date,
                    'property_cost': rec.property_cost,
                    'income': rec.income,
                    'profit_ratio': rec.profit_ratio,
                    'company_ratio': rec.company_ratio,
                    'company_profit': rec.company_profit,
                    'share_value': rec.share_value,
                    'share_profit': rec.share_profit,
                })]
            })

    '''

    def create_expense_move(self):
        value_ids = []
        total_debit = 0.000
        total_credit = 0.000
        move = None

        if not self.property_id.expenss_account_id:
            raise UserError (_ ("Please enter the expense account of the real estate (%s)") % (self.property_id.name))

        # creating debit lines for expensess and grouping payment 
        for line in self.line_ids:
            if line.calculate_profit:
                unit_cost = round(line.unit_cost, 2)
                value_ids.append((0, 0, {
                    'debit': unit_cost,
                    'credit': 0.0,
                    'partner_id': line.unit_id.buyer_id.id,
                    'account_id': self.account_id.id,
                    'name': line.unit_id.unit_name,
                    'analytic_account_id': self.account_analytic_id.id,
                }))
                total_debit += unit_cost

        if total_debit > 0:
            # Create the initial credit line
            credit_line = {
                'debit': 0.0,
                'credit': round(total_debit, 2),
                'name': self.property_id.name,
                'account_id': self.property_id.expenss_account_id.id,
                'analytic_account_id': self.account_analytic_id.id,
            }
            total_credit = round(total_debit, 2)
            value_ids.append((0, 0, credit_line))

            # Adjust the last line to ensure balance
            if round(total_debit, 2) != round(total_credit, 2):
                difference = round(total_debit - total_credit, 2)
                if difference > 0:
                    value_ids[-1]['credit'] += difference
                else:
                    value_ids[-1]['debit'] -= difference
            
            move = self.env['account.move'].create({
                'company_id': self.company_id.id,
                'journal_id': self.journal_id.id,
                'date': fields.Date.today(),
                'ref': self.name,
                'line_ids': value_ids,
            })

            self.move_id = move

        #move_id.post()
        return move
    '''

    def create_profit_move(self):
        value_ids = []
        total_debit = 0.000
        total_credit = 0.000
        profit_move = None
        
        if not self.property_id.income_account_id:
            raise UserError (_ ("Please enter the income account of the real estate (%s)") % (self.property_id.name))

        # creating debit lines for expensess and grouping payment 
        for line in self.line_ids:
            if line.calculate_profit:
                amount = round(line.amount, 2)
                value_ids.append((0, 0, {
                    'debit': amount,
                    'credit': 0.0,
                    'partner_id': line.unit_id.buyer_id.id,
                    'account_id': self.profit_account_id.id,
                    'name': line.unit_id.unit_name,
                    'analytic_account_id': self.profit_account_analytic_id.id,
                }))
                total_debit += amount

        if total_debit > 0:
            # Create the initial credit line
            credit_line = {
                'debit': 0.0,
                'credit': round(total_debit, 2),
                'name': self.property_id.name,
                'account_id': self.property_id.income_account_id.id,
                'analytic_account_id': self.profit_account_analytic_id.id,
            }
            total_credit = round(total_debit, 2)
            value_ids.append((0, 0, credit_line))

            # Adjust the last line to ensure balance
            if round(total_debit, 2) != round(total_credit, 2):
                difference = round(total_debit - total_credit, 2)
                if difference > 0:
                    value_ids[-1]['credit'] += difference
                else:
                    value_ids[-1]['debit'] -= difference
            
            profit_move = self.env['account.move'].create({
                'company_id': self.company_id.id,
                'journal_id': self.profit_journal_id.id,
                'date': fields.Date.today(),
                'ref': self.name,
                'line_ids': value_ids,
            })

            self.profit_move_id = profit_move

        #move_id.post()
        return profit_move
    '''


class ProfitsCountLine(models.Model):

    _name = 'profits.count.line'
    _description = 'Profits Count Line'
    _rec_name='line_id'

    line_id = fields.Many2one('profits.count')
    unit_id = fields.Many2one('real.estate.units', string="Unit")
    property_floors = fields.Many2one('floors.model', related='unit_id.property_floors', string="Floors Number")
    property_type_id = fields.Many2one('real.estate.type','Unit Type', related='unit_id.property_type_id')
    property_type = fields.Selection(string="Unit State", related='unit_id.property_type')
    unit_space = fields.Float('real.estate', related='unit_id.unit_space')
    unit_amount= fields.Monetary(string="Unit Price", related='unit_id.unit_amount')
    profit_calculated = fields.Boolean('Profit Calculated?', track_visibility='onchange', related='unit_id.profit_calculated')
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency")
    space = fields.Float(string="Instrument Space", track_visibility='onchange')
    unit_cost = fields.Float(string="Unit Construction Cost", compute='_compute_unit_construction_cost', store=True)
    amount = fields.Float(string="Unit Profit", compute='_compute_unit_amount', store=True)
    calculate_profit = fields.Boolean('Calculate', default=False, track_visibility='onchange')
    profit_id = fields.Many2one('real.estate','Base Property', track_visibility='onchange')

    @api.depends('unit_space', 'line_id.construction_cost', 'line_id.line_ids.unit_space')
    def _compute_unit_construction_cost(self):
        for rec in self:
            if rec.line_id:
                total_space = sum(line.unit_space for line in rec.line_id.line_ids)
                if total_space > 0:
                    rec.unit_cost = rec.unit_space * (rec.line_id.construction_cost / total_space)
                else:
                    rec.unit_cost = 0

    @api.depends('unit_space', 'unit_cost')
    def _compute_unit_amount(self):
        for rec in self:
            rec.amount = rec.unit_amount - rec.unit_cost

class PropertyProfitsCount(models.Model):

    _name = 'property.profits.count'
    _description = 'Property Profits Count'
    _rec_name='property_line_id'

    line_id = fields.Many2one('profits.count')
    property_line_id = fields.Many2one('profits.count')
    date = fields.Date(string="Date")
    property_cost = fields.Float(string="Total Property Cost")
    income = fields.Float(string="Total Income")
    profit = fields.Float(string="Total Profit")
    profit_ratio = fields.Float(string="Profit Ratio")
    company_ratio = fields.Float(string="Company Ratio")
    company_profit = fields.Float(string="Company Profit")
    share_value = fields.Float(string="Share Value")
    share_profit = fields.Float(string="Earnings per Share Ratio")
    profit_id = fields.Many2one('real.estate','Base Property', track_visibility='onchange')
    

