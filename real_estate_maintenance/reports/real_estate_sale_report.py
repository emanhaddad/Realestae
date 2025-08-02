# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime, timedelta


class RealEstateSaleReport(models.Model):
    _name = "real.estate.sale.report"
    _description = "Real Estate Sale Report"
    _auto = False

    name = fields.Char(string="Name")
    sales_user_id = fields.Many2one("res.users", string="Sales person")
    partner_id = fields.Many2one("res.partner", string="Customer")
    date = fields.Date(string='Date')
    unit_id = fields.Many2one('real.estate.units', string="Unit")
    property_type_id = fields.Many2one('real.estate.type', string='Unit Type', related='unit_id.property_type_id')
    amount = fields.Monetary(string='Amount')
    commission = fields.Monetary(string='Total of Commissions')
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency",default=lambda self: self.env.company.currency_id.id, tracking=True)
    

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'real_estate_sale_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW real_estate_sale_report AS (
                SELECT
                    rs.id AS id,
                    rs.name AS name,
                    rs.sales_user_id AS sales_user_id,
                    rs.partner_id AS partner_id,
                    rs.date AS date,
                    rs.unit_id AS unit_id,
                    rs.amount AS amount,
                    rs.commission AS commission
                FROM
                    real_estate_sale rs
                WHERE
                    rs.sale_type = 'sale'
            )
        """)
