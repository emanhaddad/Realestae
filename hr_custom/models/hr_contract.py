# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models


class hr_contract(models.Model):
    _inherit = 'hr.contract'

    housing_allowance = fields.Float(string="Housing Allowance", )
    transport_allowance = fields.Float(string="Transport Allowance", )
    other = fields.Float(string="Other", )