# -*- coding: utf-8 -*-


from odoo import api, fields, models, _

class res_company(models.Model):
    _inherit = 'res.company'
    
    income_journal_id = fields.Many2one(
        string="Income Journal",
        comodel_name="account.journal",
        domain="[('type', '=', 'sale')]",
    )


    account_id = fields.Many2one(
        string="Income Account",
        comodel_name="account.account",

    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    income_journal_id = fields.Many2one(
        string="Income Journal",
        comodel_name="account.journal",
        domain="[('type', '=', 'sale')]",
        related="company_id.income_journal_id",
        readonly=False,
    )

    account_id = fields.Many2one(
        string="Income Account",
        comodel_name="account.account",
        related="company_id.account_id",
        readonly=False,

    )