# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.

import time
from datetime import datetime, date, timedelta
from odoo.tools import misc, DEFAULT_SERVER_DATE_FORMAT
from odoo import models, fields, api, _
from odoo.exceptions import Warning


class PartsWorkOrder(models.TransientModel):
    _name = 'parts.work.order'
    _description = 'Parts Work Order'

    part_ids = fields.One2many('add.parts.work.order', 'wizard_part_id',
                               string='Used Parts')

    def add_part_on_work_order(self):
        '''
            this function gets parts from parts.work.order wizard and add them
            to fleet.vehicle.log.services as task lines
        '''
        maintenance_request = self.env['maintenance.request']
        parts_used_obj = self.env["task.line"]
        for rec_main in self:
            for rec in rec_main.part_ids:
                vals = {}
                if self._context.get('active_id', False):
                    vals.update({'fleet_service_id':
                                 self._context['active_id']})
                    if rec.product_id:
                        vals.update({'product_id': rec.product_id.id})
                    if rec.name:
                        vals.update({'name': rec.name})
                    if rec.qty:
                        vals.update({'qty': rec.qty})
                    vals.update({'encoded_qty': rec.encoded_qty})
                    vals.update({'qty_hand': rec.qty_hand})
                    if rec.product_uom:
                        vals.update({'product_uom': rec.product_uom.id})
                    if rec.price_unit:
                        vals.update({'price_unit': rec.price_unit})
                    if rec.date_issued:
                        vals.update({'date_issued': rec.date_issued})
                    if rec.old_part_return:
                        vals.update({'old_part_return': rec.old_part_return})
                    
                    
                    parts_used_obj.create(vals)
        if self._context.get('active_id', False):
            for work_order in maintenance_request.browse([self._context.get('active_id')]):
                work_order.close_reopened_wo()

class AddPartsWorkOrder(models.TransientModel):
    _name = 'add.parts.work.order'
    _description = 'Add Parts Work Order'

    wizard_part_id = fields.Many2one('parts.work.order', string='PartNo')
    product_id = fields.Many2one('product.product', string='Product No',
        #domain="[('is_spare_part','=',True)]"
        )
    qty = fields.Float(string='Used')
    old_part_return = fields.Boolean(string='Old Part Returned?')

    price_unit = fields.Float(string='Unit Cost')
    name = fields.Char(string='Part Name', size=124, translate=True)
    qty_hand = fields.Float(string='Qty on Hand', help='Quantity on Hand')
    encoded_qty = fields.Float(string='Qty for Encoding', help='Quantity that can be used')
    product_uom = fields.Many2one('uom.uom', string='UOM')
    date_issued = fields.Datetime(string='Date issued')

    dummy_price_unit = fields.Float(string='Dummy Unit Cost')
    dummy_name = fields.Char(string='Part Name', size=124, translate=True)
    dummy_qty_hand = fields.Float(string='Dummy Qty on Hand', help='Qty on Hand')
    dummy_encoded_qty = fields.Float(string='Dummy Qty for Encoding',help='Quantity that can be used')
    dummy_product_uom = fields.Many2one('uom.uom', string='Dummy UOM')
    dummy_date_issued = fields.Datetime(string='Dummy Date issued')

    def get_qty(self):
        warehouse_id = self.env['maintenance.request'].browse(
            [self._context.get('active_id')])[0].warehouse_id
        quant_ids = self.env['stock.quant'].search([('location_id','=',warehouse_id.id),('product_id','=',self.product_id.id)])
        return sum(quant.quantity for quant in quant_ids)

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            unit_price = self.product_id.standard_price
            product_uom_data = self.product_id.uom_id.id
            part_name = self.product_id.name or ''
            qty = self.get_qty()
            if qty <= 0:
                raise Warning(_("You can\'t select part which has zero quantity!"))

            self.price_unit = unit_price
            self.qty_hand = qty
            self.qty = 0.0
            self.product_uom = product_uom_data
            self.name = part_name
            self.dummy_qty_hand = qty
            self.dummy_price_unit = unit_price
            self.dummy_product_uom = product_uom_data
            self.dummy_name = part_name

    @api.onchange('qty', 'encoded_qty')
    def onchange_used_qty(self):
        if self.product_id:
            if self.get_qty() < self.qty:
                self.qty = 0.0
                raise Warning(_("You can\'t enter used quantity greater than product quantity on hand !"))

class EditPartsWorkOrder(models.Model):
    _name = 'edit.parts.work.order'
    _description = 'Edit Parts Work Order'

    part_ids = fields.One2many('task.line', 'wizard_parts_id',
                               string='Used Parts')

    @api.model
    def default_get(self, fields):
        if self._context is None:
            self._context = {}
        res = super(EditPartsWorkOrder, self).default_get(fields)
        maintenance_request_obj = self.env['maintenance.request']
        work_order_line_ids = []
        if self._context.get('active_id'):
            work_order_rec = maintenance_request_obj.browse(self._context['active_id'])
            for work_order_line in work_order_rec.parts_ids:
                work_order_line_ids.append(work_order_line.id)
        res.update({'part_ids': work_order_line_ids})
        return res

    def save_part_on_work_order(self):
        maintenance_request_obj = self.env['maintenance.request']
        cr, uid, context = self.env.args
        context = dict(context)
        if context.get('active_id', False):
            for work_order in maintenance_request_obj.browse([context['active_id']]):
                work_order.close_reopened_wo()

class TaskLine(models.Model):
    _inherit = 'task.line'

    wizard_parts_id = fields.Many2one('edit.parts.work.order',string='Parts Used')
