
from odoo import api, fields, models


class RealEstate(models.Model):

    _inherit = 'real.estate'

  
    expenss_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Expenss Analytic Account",
        tracking=True

    )
    expenss_account_id = fields.Many2one(
        string="Expenss Account",
        comodel_name="account.account",
        tracking=True
    )


class real_estate_units(models.Model):

    _inherit = 'real.estate.units'


    expenss_analytic_id = fields.Many2one(
        comodel_name='account.analytic.account',
        string="Expenss Analytic Account",
        tracking=True
    )
    expenss_account_id = fields.Many2one(
        string="Expenss Account",
        comodel_name="account.account",
        tracking=True
    )

