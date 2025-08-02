
from odoo import api, fields, models


class RealEstate(models.Model):

    _inherit = 'real.estate'

  
    analytic_id = fields.Many2one('account.analytic.account',string="Income Analytic Account")
    income_account_id = fields.Many2one(
        string="Income Account",
        comodel_name="account.account",
        tracking=True
    )

    @api.onchange('project_id')
    def onchange_project(self):
        if self.project_id and self.project_id.analytic_account_id:
            self.analytic_id = self.project_id.analytic_account_id.id



class real_estate_units(models.Model):

    _inherit = 'real.estate.units'


    analytic_id = fields.Many2one('account.analytic.account',string="Income Analytic Account")
    income_account_id = fields.Many2one(
        string="Income Account",
        comodel_name="account.account",
        tracking=True
    )




