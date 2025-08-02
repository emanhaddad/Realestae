# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import time
from datetime import datetime, date, timedelta
from odoo import models, fields, _, api
from odoo.tools import misc, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import Warning, ValidationError


class TaskLine(models.Model):
    _name = 'task.line'
    _description = 'Task Line'

    def _amount_line(self):
        for line in self:
            price = line.price_unit * line.qty
            line.total = price

    partshist_id = fields.Integer(string='Parts History ID',help="Take this field for data migration")
    task_id = fields.Many2one('service.task', string='task reference')
    fleet_service_id = fields.Many2one('maintenance.request',string='Vehicle Work Order')
    product_id = fields.Many2one('product.product', string='Product No',required=True)
    name = fields.Char(string='Part Name', size=124, translate=True)
    encoded_qty = fields.Float(string='Qty for Encoding',help='Quantity that can be used')
    qty_hand = fields.Float(string='Qty on Hand', help='Quantity on Hand')
    dummy_encoded_qty = fields.Float(string='Encoded Qty', help='Quantity that can be used')
    qty = fields.Float(string='Used')
    product_uom = fields.Many2one('uom.uom', string='UOM', required=True)
    price_unit = fields.Float(string='Unit Cost')
    total = fields.Float(compute="_amount_line",  string='Total Cost')
    date_issued = fields.Datetime(string='Date issued')
    old_part_return = fields.Boolean(string='Old Part Returned?')
    issued_by = fields.Many2one('res.users', string='Issued By', default=lambda self: self._uid)
    is_deliver = fields.Boolean(string="Is Deliver?")
    description = fields.Text(string="Description", )
    state = fields.Selection(
        string="State",
        selection=[
            ('draft', 'Draft'),
            ('waiting_approval', 'Waiting Work Shop Manager Approval'),
            ('confirm', 'Confirmed'),
        ],default='confirm',readonly=True
    )
    estimated_end = fields.Date(string="Estimated End Life Time", readonly=True)
    return_qty = fields.Float(string="Returend QTY", )

    def return_item(self):
        '''
            * return some item form qty
        '''
        if self.return_qty > self.qty:
            raise Warning(_('You can\'t return more than quanity !'))
        location_from_id = False
        
        for picking_line in self.fleet_service_id.out_going_id.move_ids_without_package:
            if picking_line.product_id.id == self.product_id.id:
                location_from_id = picking_line.location_dest_id.id
                break
        if not location_from_id:
            raise Warning(_("Spare Part not found on delivery order are you suer you deliverd this spare part"))

        in_pick_type = self.env['stock.picking.type'].search([('sequence_code', '=', 'IN'),('default_location_dest_id','=',self.fleet_service_id.warehouse_id.id)], limit=1)
        
        if not in_pick_type:
            raise Warning(_("Select Location has no default desitnation location ,, please select it first"))

        ship_id = self.env['stock.picking'].create({
            'picking_type_id':in_pick_type.id,
            'location_id': location_from_id,
            'location_dest_id': self.fleet_service_id.warehouse_id.id ,
        })
        stock_move = self.env['stock.move'].create({
            'product_id': self.product_id.id,
            'name': self.product_id.name or '',
            'product_uom_qty': self.return_qty,
            'quantity_done':self.return_qty,
            'product_uom': self.product_uom and self.product_uom.id or False,
            'location_id': location_from_id,                    
            'location_dest_id': self.fleet_service_id.warehouse_id.id ,
            'price_unit': self.price_unit,
            'picking_type_id': in_pick_type.id,
            'picking_id':ship_id.id,
        })
        ship_id.action_confirm()
        ship_id.action_assign()
        ship_id.button_validate()
        self.qty = self.qty - self.return_qty
        self.fleet_service_id.old_parts_incoming_ship_id = ship_id.id
        self.fleet_service_id.close_reopened_wo()

    @api.constrains('qty')
    def _check_used_qty(self):
        for rec in self:
            if rec.qty <= 0 and not rec.return_qty:
                raise Warning(_('You can\'t enter used quanity as Zero!'))
    
    @api.model
    def create(self, vals):
        """
        Overridden create method to add the issuer
        of the part and the time when it was issued.
        -----------------------------------------------------------
        @param self : object pointer
        """
        product_obj = self.env['product.product']
        if not vals.get('issued_by', False):
            vals.update({'issued_by': self._uid})
        if not vals.get('date_issued', False):
            vals.update({'date_issued':
                         time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})

        if vals.get('fleet_service_id', False) and \
                vals.get('product_id', False):
            task_line_ids = self.search([
                     ('fleet_service_id', '=', vals['fleet_service_id']),
                     ('product_id', '=', vals['product_id'])])
            if task_line_ids:
                product_rec = product_obj.browse(vals['product_id'])
                warrnig = 'You can not have duplicate parts assigned !!! \n Part No :- ' + str(product_rec.default_code)
                raise Warning(_(warrnig))
        return super(TaskLine, self).create(vals)

    def write(self, vals):
        """
        Overridden write method to add the issuer of the part
        and the time when it was issued.
        ---------------------------------------------------------------
        @param self : object pointer
        """
        if vals.get('product_id', False)\
            or vals.get('qty', False)\
            or vals.get('product_uom', False)\
            or vals.get('price_unit', False)\
                or vals.get('old_part_return') in (True, False):
                vals.update({'issued_by': self._uid,
                             'date_issued':
                             time.strftime(DEFAULT_SERVER_DATETIME_FORMAT)})
        return super(TaskLine, self).write(vals)

    def confirm(self):
        for line in self : 
            line.state = 'confirm'
            flag = True
            for order_line in line.fleet_service_id.parts_ids:
                if order_line.state != 'confirm':
                    flag = False
            if flag:
                line.fleet_service_id.close_reopened_wo()

    @api.onchange('date_issued')
    def check_onchange_part_issue_date(self):
        context_keys = self._context.keys()
        if 'date_open' in context_keys and self.date_issued:
            date_open = self._context.get('date_open', False)
            current_date = time.strftime(DEFAULT_SERVER_DATE_FORMAT)
            if not self.date_issued >= date_open and \
                    not self.date_issued <= current_date:
                self.date_issued = False
                raise Warning(_('You can\t enter \
                        parts issue either open work order date or in \
                           between open work order date and current date!'))

    @api.onchange('product_id')
    def onchange_product_id(self):
        #team_trip_obj = self.env['fleet..team']
        if self.product_id:
            rec = self.product_id
            if rec.in_active_part:
                self.product_id = False
                self.name = False
                self.qty = 1.0
                self.product_uom = False
                self.price_unit = False
                self.date_issued = False
                self.old_part_return = False
                raise Warning(_('You can\'t select \
                        part which is In-Active!'))
            unit_price = rec.standard_price
            product_uom_data = rec.uom_id.id
            part_name = rec.name or ''
            if not rec.qty_available:
                self.product_id = False
                self.name = False
                self.qty = 1.0
                self.product_uom = False
                self.price_unit = False
                self.date_issued = False
                self.old_part_return = False
                raise Warning(_('You can\'t select part which has zero quantity!'))
            self.price_unit = unit_price
            self.qty = 0
            self.product_uom = product_uom_data
            self.name = part_name

    @api.onchange('product_id', 'qty', 'encoded_qty')
    def onchange_used_qty(self):
        pass