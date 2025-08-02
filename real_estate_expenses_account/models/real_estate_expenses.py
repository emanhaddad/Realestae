from odoo import models, fields, api ,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, AccessError,UserError

class expense_request(models.Model):
    _inherit = "expense.request"

   
    # move_id = fields.Many2one('account.move', string='Move',required=False,readonly=True)
    # state = fields.Selection(selection_add=[('transferd', 'Transferd')])
   
    # payment_method = fields.Many2one(
    #     string="Payment Method/ Journal",
    #     comodel_name="account.journal",
    #     domain="[('type', 'in', ('cash','bank'))]",
    # )
    # exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type')
    # count_payment = fields.Integer(compute='_compute_je', string="Payment")
   
 

    def create_move(self):
        if self.move_id:
            raise ValidationError(_("Sorry !! this request is almost Transferd"))
        
        journal_id = self.env.user.company_id.expenses_journal_id


        if self.unit_id:
            expenss_analytic_id = self.unit_id.expenss_analytic_id if self.unit_id.expenss_analytic_id \
            else self.property_id.expenss_analytic_id

            account_id = self.unit_id.expenss_account_id if self.unit_id.expenss_account_id \
            else self.property_id.expenss_account_id

            account_id = self.env.user.company_id.expenss_account_id if not account_id else account_id

        else:
            expenss_analytic_id = self.property_id.expenss_analytic_id
            account_id = self.property_id.expenss_account_id if self.property_id.expenss_account_id \
            else self.env.user.company_id.expenss_account_id


        if not self.property_id.expenss_account_id:
            raise ValidationError(_("Please enter the unit expense account"))

        move_vals = {
            'journal_id': self.payment_method.id,
            # 'move_type': 'in_receipt',
            'company_id': self.company_id.id,
            'ref': _("Expense of %s", self.property_id.name),
            'date': self.date or fields.Date.today(),
            'line_ids': [(0, 0, {
                'name':  _(self.description),
                'account_id': self.property_id.expenss_account_id.id,
                'debit': 0,
                'analytic_account_id':expenss_analytic_id.id,
                'credit': abs(self.amount),})
            ,(0, 0, {
                'name':_(""),
                'account_id': self.payment_method.default_account_id.id,
                'debit':abs(self.amount),
                'credit':0})],
            }

        account_move = self.env['account.move'].create(move_vals)
        account_move._post()
        self.write({
            'move_id' : account_move,
        })

    # def transfer(self):
    #     if not self.exchange_type_id:
    #         raise UserError("Please select the exchange type")
    #     if not self.real_estate_id.expenss_account_id.id:
    #         raise UserError("Please enter the expense account of the real estate")
    #     last_cash_order = self.env['cash.order'].search([], order='id desc', limit=1)
    #     if last_cash_order:
    #         last_sequence = int(last_cash_order.name.split('/')[-1])
    #     else:
    #         last_sequence = 0
    #     new_sequence = last_sequence + 1
    #     new_cash_order_name = f'CP/{new_sequence:02d}'
    #     payment_id = self.env['cash.order'].create({
    #                 'state': 'general',
    #                 'name': new_cash_order_name,
    #                 'date': self.date,
    #                 'exchange_type_id' : self.exchange_type_id.id,
    #                 'partner_id': self.supervisor.id,
    #                 'amount' : self.amount,
    #                 'journal_id' : self.journal_id.id,
    #                 'disc' : self.name + ' ' + 'طلب مصروف',
    #                 'maintenance_request_ids' : self.id,
    #                 'order_line_ids': [(0, 0, {
    #                     'description': 'أمر صرف مصروف',
    #                     'account_id': self.property_id.expenss_account_id.id,
    #                     'amount': self.amount,
    #                     'state': 'general',
    #                 })],
    #             })

    #     payment_id.action_finance()
    #     self.move_id = payment_id.move_id.id
    #     # self.create_move()
    #     return self.write({'state': 'transferd'})

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
    #         'domain': [('maintenance_request_ids', '=', self.id)],

    #     }

    # def _compute_je(self):
    #     if self.move_id:
    #         self.count_payment = 1
    #     else:
    #         self.count_payment = 0