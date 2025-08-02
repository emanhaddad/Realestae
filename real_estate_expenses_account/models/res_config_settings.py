# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

class res_company(models.Model):
    _inherit = 'res.company'
    
    expenses_journal_id = fields.Many2one(
        string="Expenses Journal",
        comodel_name="account.journal",
        domain="[('type', '=', 'purchase')]",
    )

    expenss_account_id = fields.Many2one(
        string="Expenss Account",
        comodel_name="account.account",

    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    expenses_journal_id = fields.Many2one(
        string="Expenses Journal",
        comodel_name="account.journal",
        domain="[('type', '=', 'purchase')]",
        related="company_id.expenses_journal_id",
        readonly=False,
    )

    expenss_account_id = fields.Many2one(
        string="Expenss Account",
        comodel_name="account.account",
        related="company_id.expenss_account_id",
        readonly=False,

    )