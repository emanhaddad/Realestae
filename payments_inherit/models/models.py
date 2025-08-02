# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import ValidationError, UserError

class payments_inherit(models.Model):
    _inherit = "account.payment"

    cost_center = fields.Many2one("account.analytic.account")
    destination_account_id = fields.Many2one("account.account")

    def _prepare_move_line_default_vals(self, write_off_line_vals=None):
        """
        Override the _prepare_move_line_default_vals method to include the selected cost center in the journal entry
        and perform a balance check for outbound payments.
        """
        # Perform the default preparation for move line values
        line_vals_list = super(payments_inherit, self)._prepare_move_line_default_vals(write_off_line_vals=write_off_line_vals)

        # Perform additional processing for outbound payments
        # if self.payment_type == 'outbound':
            # Calculate the remaining balance of the payment credit account
            # remaining_balance = sum(self.env['account.move.line'].search([
                # ('account_id', '=', self.journal_id.payment_credit_account_id.id)
            # ]).mapped('balance'))

            # Check if the payment amount exceeds the remaining balance
            # if self.amount > remaining_balance:
                # Raise a warning message if the balance is insufficient
                # raise UserError(_("The payment amount (%s) exceeds the remaining balance (%s) in account %s.") % (
                    # self.amount, remaining_balance, self.journal_id.payment_credit_account_id.name))

        # Add cost center to move line values
        for line_vals in line_vals_list:
            if line_vals.get('account_id') == self.destination_account_id.id:
                line_vals['analytic_account_id'] = self.cost_center.id
            elif line_vals.get('account_id') == self.journal_id.payment_debit_account_id.id:
                line_vals['analytic_account_id'] = self.cost_center.id
            elif line_vals.get('account_id') == self.journal_id.payment_credit_account_id.id:
                line_vals['analytic_account_id'] = self.cost_center.id

        return line_vals_list
