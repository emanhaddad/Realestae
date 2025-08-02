from odoo import api, fields, models, _

class HrBonus(models.Model):

    _name = 'hr.bonus'
    
    name = fields.Char('Name',states={'draft': [('readonly', False)]},readonly=True,required=True)
    employee_id = fields.Many2one('hr.employee','employee',states={'draft': [('readonly', False)]},readonly=True,required=True)
    amount = fields.Float(string="Amount", states={'draft': [('readonly', False)]},readonly=True)
    account_id = fields.Many2one('account.account',)
    journal_id = fields.Many2one('account.journal',)
    bonus_date = fields.Date('Date',states={'draft': [('readonly', False)]},readonly=True, required=True)
    bonus_type= fields.Selection([('bonus', 'Bonus')])
    move_id = fields.Many2one('account.move','Move',readonly=True)
    note = fields.Text("Note", states={'draft': [('readonly', False)]},readonly=True)
    state= fields.Selection([('draft', 'Draft'),('dept_manager', 'Department Manager Approved'),('financial_manager', 'Financial Manager Approved'),('general_manager', 'General Manager Approved'),('paid', 'Paid')],default="draft")

    def action_department_manager(self):
        for rec in self:
            rec.state = 'dept_manager'

    def action_financial_manager(self):
        for rec in self:
            rec.state = 'financial_manager'

    def action_general_manager(self):
        for rec in self:
            rec.state = 'general_manager'

    def create_payment(self):
        move_id = self.env['account.move'].sudo().create({
                    'move_type': 'in_receipt',
                    'partner_id': self.employee_id.address_home_id.id,
                    'journal_id': self.journal_id.id or False,
                    'date': fields.Date.context_today(self),
                    'invoice_line_ids':[(0, 0, {'name': self.name,
                                                 'account_id': self.account_id.id,
                                                 'partner_id': self.employee_id.address_home_id.id,
                                                 'price_unit': self.amount,
                                                 'quantity': 1})],
                })

        #move_id.post()
        self.move_id = move_id.id    
        self.state = 'paid'
