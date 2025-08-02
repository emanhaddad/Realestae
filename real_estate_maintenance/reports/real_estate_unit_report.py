# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models, tools
from datetime import datetime, timedelta



class RealEstateUnitReport(models.Model):
    _name = "real.estate.unit.report"
    _description = "Real Estate Unit"
    _auto = False

    code = fields.Char(string='Code')
    unit_name = fields.Char(string='Unit Name')
    date = fields.Date('Date')
    property_type_id = fields.Many2one('real.estate.type','Unit Type')
    base_property_id = fields.Many2one('real.estate','Base Property')
    property_type = fields.Selection([
        ('ready','Ready'),
        ('under_construction','Under construction'),
        ('final_prepare','Final prepare')])
    property_floors = fields.Many2one('floors.model' ,string="Floor Number")
    property_rooms = fields.Integer("Rooms Number")
    buyer_id = fields.Many2one('res.partner', 'Buyer')
    owner_id = fields.Many2one('res.partner', 'Owner')
    unit_amount= fields.Monetary(string="Unit amount")
    unit_taxes= fields.Monetary(string="Unit taxes")
    unit_price= fields.Monetary(string="Unit Price")
    unit_space=fields.Float(string='Space')
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", oldname='currency')
    commission_type= fields.Selection([('fixed','Fixed'),('ratio','Ratio')])
    unit_commission= fields.Monetary(string="Unit commission")
    state = fields.Selection([
        ('available', 'Available'),
        ('delegated', 'Delegated'),
        ('booked', 'Booked'),
        ('sold','Sold'),
        ('delivered','Delivered'),
        ('re_sold','Resold'),
        ('authorized','Authorized')])

    def init(self):
        tools.drop_view_if_exists(self.env.cr, 'real_estate_unit_report')
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW real_estate_unit_report AS (
                SELECT
                    rsu.id as id,
                    rsu.code,
                    CONCAT(bp.name, '-', rsu.code) as unit_name,
                    rsu.date,
                    rsu.property_type_id,
                    rsu.base_property_id,
                    rsu.property_type,
                    rsu.property_floors,
                    rsu.property_rooms,
                    rsu.unit_space,
                    rsu.buyer_id,
                    rsu.owner_id,
                    rsu.unit_price,
                    rsu.unit_amount,
                    rsu.unit_taxes,
                    rsu.commission_type,
                    rsu.unit_commission,
                    rsu.state
                FROM 
                    real_estate_units rsu
                LEFT JOIN 
                    real_estate bp ON rsu.base_property_id = bp.id
            )
        """)