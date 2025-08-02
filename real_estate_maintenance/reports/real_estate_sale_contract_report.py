# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime, timedelta

class RealEstateContractReport(models.Model):
    _name = "real.estate.contract.report"
    _description = "Real Estate Unit - Sales Contracts"
    _auto = False

    contract_no = fields.Char('Contract No')
    partner_id = fields.Many2one("res.partner", string="Customer")
    contract_amount = fields.Monetary(string='Contract Amount')
    unit_id = fields.Many2one('real.estate.units', string='Unit')
    date = fields.Date('Date')
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency")
    total_paid = fields.Monetary(string='Total Paid Amount', store=True)
    remaining_amount = fields.Monetary(string='Remaining Amount', store=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'real_estate_contract_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW real_estate_contract_report AS (
                SELECT
                    rc.id AS id,
                    rc.contract_no AS contract_no,
                    rc.partner_id AS partner_id,
                    rc.contract_amount AS contract_amount,
                    rc.unit_id AS unit_id,
                    rc.create_date::date AS date,
                    rc.currency_id AS currency_id,
                    COALESCE(SUM(rp.paid_amount), 0) AS total_paid,
                    (rc.contract_amount - COALESCE(SUM(rp.paid_amount), 0)) AS remaining_amount
                FROM
                    realestate_contract_model rc
                    LEFT JOIN rent_contract_payment rp ON rp.analytic_id = rc.id
                WHERE
                    rc.contract_partner_type = 'sale'
                GROUP BY
                    rc.id, rc.contract_no, rc.partner_id, rc.contract_amount, rc.unit_id, rc.create_date, rc.currency_id
            )
        """)