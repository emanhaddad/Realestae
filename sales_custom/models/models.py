#-*- coding: utf-8 -*-

from odoo import models, fields, api


class SalesCustom(models.Model):

    _inherit = 'crm.lead'

    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        related='unit_id.base_property_id',)
    unit_id = fields.Many2one('real.estate.units',
        string="Unit")


class ProductCustom(models.Model):

    _inherit = 'product.template'

    investment_ok = fields.Boolean('Can be Investment', default=False)
    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        related='unit_id.base_property_id',)
    unit_id = fields.Many2one(
        'real.estate.units',
        string="Unit")
    cost_center = fields.Many2one("account.analytic.account")


class ProductCustom(models.Model):
    _inherit = 'sale.order'

    product_id = fields.Many2one(
        'product.product',
        string='Product',
        change_default=True,
        ondelete='restrict',
        check_company=True)
    #domain="[('investment_ok', '=', True), '|', ('company_id', '=', False), ('company_id', '=', company_id)]",

class res_partner(models.Model):
    _inherit = 'res.partner'

    id_partner_number = fields.Char(string='ID Number')
    # date = fields.Date(string='Sale Date', index=True,)
    # delivery_date = fields.Date(string='Delivery Date')
