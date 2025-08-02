# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from datetime import datetime, date
from odoo.exceptions import Warning, UserError

class MaterialPurchaseRequisition(models.Model):
    _inherit = 'material.purchase.requisition'

    task_user_id = fields.Many2one(
        'res.users',
        related='custom_task_id.user_id',
        string='Task / Job Order User'
    )
    equipment_machine_total = fields.Float(
        compute='compute_equipment_machine',
        string='Equipment / Machinery Cost',
        store=True,
    )
    worker_resource_total = fields.Float(
        compute='compute_equipment_machine',
        string='Worker / Resource Cost',
        store=True,
    )
    work_cost_package_total = fields.Float(
        compute='compute_equipment_machine',
        string='Work Cost Package',
        store=True,
    )
    subcontract_total = fields.Float(
        compute='compute_equipment_machine',
        string='Subcontract Cost',
        store=True,
    )
            

    @api.depends('requisition_line_ids',
                 'requisition_line_ids.product_id',
                 'requisition_line_ids.product_id.boq_type')
    def compute_equipment_machine(self):
        eqp_machine_total = 0.0
        work_resource_total = 0.0
        work_cost_package_total = 0.0
        subcontract_total = 0.0
        for rec in self:
            for line in rec.requisition_line_ids:
                if line.product_id.boq_type == 'eqp_machine':
                    eqp_machine_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'worker_resource':
                    work_resource_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'work_cost_package':
                    work_cost_package_total += line.product_id.standard_price * line.qty
                if line.product_id.boq_type == 'subcontract':
                    subcontract_total += line.product_id.standard_price * line.qty
            rec.equipment_machine_total = eqp_machine_total
            rec.worker_resource_total = work_resource_total
            rec.work_cost_package_total = work_cost_package_total
            rec.subcontract_total = subcontract_total