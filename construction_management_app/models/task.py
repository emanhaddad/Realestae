# -*- coding: utf-8 -*-

from odoo import models, fields, api

class MaterialPlanning(models.Model):
    _name = 'material.plan'
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return

        self.update({
            'product_uom': self.product_id.uom_po_id or self.product_id.uom_id,
            'description': self.product_id.name,
            'cost': self.product_id.standard_price,
        })


    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_uom_qty = fields.Float('Quantity', digits='Product Unit of Measure')

    cost = fields.Float(string="Cost")
    subtotal = fields.Float(string='Total', compute='_compute_subtotal', readonly=True, store=True)

    @api.depends('product_uom_qty', 'cost')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.product_uom_qty * line.cost

    product_uom = fields.Many2one('uom.uom', 'Unit of Measure')
    material_task_id = fields.Many2one('project.task', 'Material Plan Task')

class ConsumedMaterial(models.Model):
    _name = 'consumed.material'
    
    @api.onchange('product_id')
    def onchange_product_id(self):
        if not self.product_id:
            return
        self.update({
            'product_uom': self.product_id.uom_po_id or self.product_id.uom_id,
            'description': self.product_id.name,
            'cost': self.product_id.standard_price,
        })

    product_id = fields.Many2one('product.product', string='Product')
    description = fields.Char(string='Description')
    product_uom_qty = fields.Float('Quantity', digits='Product Unit of Measure')

    product_uom = fields.Many2one('uom.uom','Unit of Measure')
    cost = fields.Float(string="Cost")
    subtotal = fields.Float(string="Total", compute='_compute_subtotal', readonly=True, store=True)

    @api.depends('product_uom_qty', 'cost')
    def _compute_subtotal(self):
        for line in self:
            line.subtotal = line.product_uom_qty * line.cost

    consumed_task_material_id = fields.Many2one('project.task', 'Consumed Material Plan Task')

class ProjectTask(models.Model):
    _inherit = 'project.task'
    
    # @api.multi #odoo13
    # @api.depends('picking_ids.move_lines')
    # def _compute_stock_picking_moves(self):
    #     for rec in self:
    #         rec.ensure_one()
    #         for picking in rec.picking_ids:
    #             rec.move_ids = picking.move_lines.ids

    material_amount_planned = fields.Float(string='Planned Materials Total',
                                           compute='_compute_material_amount',
                                           readonly=True, store=True)
    material_amount_consumed = fields.Float(string='Consumed Materials Total',
                                            compute='_compute_material_amount',
                                            readonly=True, store=True)

    @api.depends('material_plan_ids', 'material_plan_ids.subtotal',
                 'consumed_material_ids', 'consumed_material_ids.subtotal')
    def _compute_material_amount(self):
        for task in self:
            task.material_amount_planned = sum(task.material_plan_ids.mapped('subtotal'))
            task.material_amount_consumed = sum(task.consumed_material_ids.mapped('subtotal'))

    @api.depends()
    def _compute_stock_picking_moves(self):
        move_ids = self.env['stock.move']
        for rec in self:
            for requisition in rec.picking_ids:
                picking_ids = self.env['stock.picking'].search([('custom_requisition_id','=',requisition.id)])
                for picking in picking_ids:
                    for move in picking.move_ids_without_package:
                        move_ids += move
            rec.move_ids = [(6,0, move_ids.ids)]

    def total_stock_moves_count(self):
        for task in self:
            task.stock_moves_count = len(task.move_ids)
            
    @api.depends('notes_ids')
    def _compute_notes_count(self):
        for task in self:
            task.notes_count = len(task.notes_ids)

    picking_ids = fields.One2many(
        'material.purchase.requisition',
        'custom_task_id',
        'Stock Pickings'
    )
    
    # picking_ids = fields.One2many(
    #     'stock.picking',
    #     'task_id',
    #     'Stock Pickings'
    # )
    move_ids = fields.Many2many(
        'stock.move',
        compute='_compute_stock_picking_moves',
    )
    
    # move_ids = fields.Many2many(
    #     'stock.move',
    #     compute='_compute_stock_picking_moves',
    #     store=True,
    # )
    material_plan_ids = fields.One2many(
        'material.plan',
        'material_task_id',
        'Material Plannings'
    )
    consumed_material_ids = fields.One2many(
        'consumed.material',
        'consumed_task_material_id',
        'Consumed Materials'
    )
    # stock_moves_count = fields.Integer(
    #     compute='total_stock_moves_count', 
    #     string='# of Stock Moves',
    #     store=True,
    # )
    stock_moves_count = fields.Integer(
        compute='total_stock_moves_count', 
        string='# of Stock Moves',
        store=True,
    )
    parent_task_id = fields.Many2one(
        'project.task', 
        string='Parent Task', 
        readonly=True
    )
    child_task_ids = fields.One2many(
        'project.task', 
        'parent_task_id', 
        string='Child Tasks'
    )
    notes_ids = fields.One2many(
        'note.note', 
        'task_id', 
        string='Notes',
    )
    notes_count = fields.Integer(
        compute='_compute_notes_count', 
        string="Notes"
    )
    
    # @api.multi #odoo13
    def view_stock_moves(self):
        for rec in self:
            stock_move_list = []
            for move in rec.move_ids:
                stock_move_list.append(move.id)
        # result = self.env.ref('stock.stock_move_action')
        result = self.env.ref('stock.stock_move_action')
        action_ref = result or False
        result = action_ref.read()[0]
        result['domain'] = str([('id', 'in', stock_move_list)])
        return result
        
    # @api.multi #odoo13
    def view_notes(self):
        for rec in self:
            res = self.env.ref('construction_management_app.action_task_note_note')
            res = res.read()[0]
            res['domain'] = str([('task_id','in',rec.ids)])
        return res
