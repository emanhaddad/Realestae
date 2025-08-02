from odoo import models, fields, api

class Supervisor(models.Model):
    _inherit = 'hr.employee'
    
    is_supervisor = fields.Boolean(string='is Supervisor')



