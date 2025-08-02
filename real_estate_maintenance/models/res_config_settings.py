# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class res_company(models.Model):
    _inherit = 'res.company'

    sale_commission = fields.Float(
        string="Sales Commission",
    )


class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    sale_commission = fields.Float(
        string="Sales Commission",
        related="company_id.sale_commission",
        readonly=False
    )