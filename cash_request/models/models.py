# -*- encoding: utf-8 -*-
# © 2017 Mackilem Van der Laan, Trustcode
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class exchange_item(models.Model):
    _name = 'exchange.item'
    _description = 'Exchange Items'

    name = fields.Char(string="Name" , required=True, tracking=True)
    department_ids = fields.Many2many(
        string="Departments",
        comodel_name="hr.department",
        relation="exchange_dep_rel",
        column1="exchange_id",
        column2="dep_id",
        tracking=True
    )



    
class res_partner(models.Model):
    _inherit = 'res.partner'

    beneficiary = fields.Boolean("beneficiary", default=False, tracking=True)


class account_move(models.Model):
    _inherit = "account.move"

    order_id = fields.Many2one(
        string="Financial Order",
        comodel_name="cash.order",
    )
