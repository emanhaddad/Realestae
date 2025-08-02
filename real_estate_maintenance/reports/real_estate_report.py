# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools

class RealEstateReport(models.Model):
    _name = "real.estate.report"
    _description = "Real Estate"
    _auto = False

    property_name = fields.Char('Property Name')
    code = fields.Char('Code')
    date = fields.Date('Date')
    property_type_id = fields.Many2one('real.estate.type', 'Property Type')
    city = fields.Char('City')
    supervisor_id = fields.Many2one("hr.employee", string="Supervisor")
    asanseer_nums = fields.Integer(string='Asanseer Nums')
    property_total_area = fields.Float("Total Area")
    property_builtup_area = fields.Float("Built-up Area")
    property_units_number = fields.Integer(string="Number of Units")
    property_charact = fields.Selection(selection=[('share', 'Share'), ('under_construc', 'Under Construction')])
    num_of_share = fields.Float(string="Planned number of shares")
    property_share_number = fields.Integer(string="Number of Shares")
    remain_share_number = fields.Integer(string="Remain Number of Shares Required")

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'real_estate_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW real_estate_report AS (
                SELECT
                    row_number() OVER () AS id,
                    line.property_name,
                    line.code,
                    line.date,
                    line.property_type_id,
                    line.property_charact,
                    line.city,
                    line.supervisor_id,
                    line.asanseer_nums,
                    line.property_total_area,
                    line.property_builtup_area,
                    line.num_of_share,
                    line.property_share_number,
                    line.remain_share_number,
                    count(units.id) AS property_units_number
                FROM (
                    SELECT
                        rs.id as code,
                        rs.name as property_name,
                        rs.date as date,
                        rs.property_type_id as property_type_id,
                        rs.property_charact as property_charact,
                        rs.city as city,
                        rs.supervisor_id as supervisor_id,
                        rs.asanseer_nums as asanseer_nums,
                        rs.property_total_area as property_total_area,
                        rs.property_builtup_area as property_builtup_area,
                        rs.num_of_share as num_of_share,
                        rs.property_share_number as property_share_number,
                        rs.remain_share_number as remain_share_number
                    FROM 
                        real_estate rs
                ) as line
                LEFT JOIN real_estate_units units ON units.base_property_id = line.code
                GROUP BY 
                    line.property_name, 
                    line.code, 
                    line.date, 
                    line.property_type_id, 
                    line.property_charact,
                    line.city, 
                    line.supervisor_id, 
                    line.asanseer_nums, 
                    line.property_total_area, 
                    line.property_builtup_area,
                    line.num_of_share,
                    line.property_share_number,
                    line.remain_share_number
            )""")
