from odoo import models, fields, api , _


class res_partner(models.Model):
	_inherit = "res.partner"

	
	equipment_count = fields.Integer(
		string='Equipment',
		compute='get_maintanance'	
	)

	maintanance_count = fields.Integer(
		string='Maintanance',
		compute='get_maintanance'
	)

	installation_count = fields.Integer(
		string='Installation',
		compute='get_maintanance'
	)
	

	def get_maintanance(self):
		equipment = self.env['maintenance.equipment'].search_count([('customer_id', '=', self.id)])
		maintanance = self.env['maintenance.request'].search_count([('equipment_id.customer_id', '=', self.id)])
		installation = self.env['equipment.installation'].search_count([('customer_id', '=', self.id)])
		self.equipment_count = equipment
		self.maintanance_count = maintanance
		self.installation_count = installation

	def open_equipment(self):
		return {
            'name': _('Equipment'),
            'domain': [('customer_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'maintenance.equipment',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

	def open_maintanance(self):
		return {
            'name': _('Maintanance'),
            'domain': [('equipment_id.customer_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'maintenance.request',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }

	def open_installation(self):
		return {
            'name': _('installation'),
            'domain': [('customer_id', '=', self.id)],
            'view_type': 'form',
            'res_model': 'equipment.installation',
            'view_id': False,
            'view_mode': 'tree,form',
            'type': 'ir.actions.act_window',
        }



    