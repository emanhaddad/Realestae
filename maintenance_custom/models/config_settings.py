# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, _

class res_company(models.Model):
    _inherit = 'res.company'
    
    after_sale_journal_id = fields.Many2one(
        string="Maintenace Journal",
        comodel_name="account.journal",
        domain="[('type', '=', 'sale')]",
    )

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    after_sale_journal_id = fields.Many2one(
        string="Maintenace Journal",
        comodel_name="account.journal",
        domain="[('type', '=', 'sale')]",
        related="company_id.after_sale_journal_id",
        readonly=False,
    )