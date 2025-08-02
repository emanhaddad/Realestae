# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date

class CustomReport(models.Model):
    _inherit = 'account.move.line'

    cost_center = fields.Many2one("account.analytic.account")
    debit = fields.Monetary(string='Debit', default=0.0, currency_field='company_currency_id')
    credit = fields.Monetary(string='Credit', default=0.0, currency_field='company_currency_id')
    balance = fields.Monetary(string='Balance', store=True,
                              currency_field='company_currency_id',
                              compute='_compute_balance',
                              help="Technical field holding the debit - credit in order to open meaningful graph views from reports")
    account_id = fields.Many2one('account.account', string='Account',
                                 index=True, ondelete="cascade",
                                 domain="[('deprecated', '=', False), ('company_id', '=', 'company_id'),('is_off_balance', '=', False)]",
                                 check_company=True,
                                 tracking=True)
    remaining_balance = fields.Monetary(string='Remaining Balance', store=True,
                                        currency_field='company_currency_id',
                                        compute='_compute_remaining_balance',
                                        help="Technical field holding the balance + debit - credit in order to open meaningful graph views from reports")

    @api.depends('debit', 'credit')
    def _compute_balance(self):
        for line in self:
            line.balance = line.debit - line.credit

    # calculate the remaining balance
    @api.depends('debit', 'credit', 'account_id')
    def _compute_remaining_balance(self):
        for line in self:
            # Calculate previous balance
            previous_balance = sum(self.search([
                ('account_id', '=', line.account_id.id),
                ('date', '<=', line.date),('id', '!=', line.id),
            ]).mapped('balance'))
            print ("previous_balance:::::::::",previous_balance)
            # Calculate remaining balance
            line.remaining_balance = previous_balance + line.debit - line.credit
