# -*- coding: utf-8 -*-

from odoo import api, fields, models, tools,_

class MaintenanceEquipment(models.Model):
    _inherit = 'maintenance.equipment'

    equipment_assign_to = fields.Selection(
        [('customer','Customer'),('department', 'Department'), ('employee', 'Employee'), ('other', 'Other')],
        string='Used By',
        required=True,
        default='customer')
    customer_id = fields.Many2one(
        string="Customer",
        comodel_name="res.partner",
        # domain="[('customer', '=', True)]",
    )

    serial_id = fields.Many2one('stock.production.lot',string='Serial Number',copy=False , readonly=True,)

class maintenance_stage(models.Model):
    _inherit = 'maintenance.stage'

    repaired_stage = fields.Boolean(string="Is Repaired Stage",)

    @api.onchange('repaired_stage')
    def _compute_field(self):
        recs = self.search([('repaired_stage','=',True)])
        for rec in recs:
            rec.write({'repaired_stage':False})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
       
      
            
    
    
