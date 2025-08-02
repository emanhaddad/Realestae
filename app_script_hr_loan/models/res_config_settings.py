# -*- coding: utf-8 -*-
##############################################################################
#
#    App-script Business Solutions
#
##############################################################################

from odoo import api, fields, models, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    company_id = fields.Many2one('res.company' , default=lambda self: self.env.user.company_id)
    max_department = fields.Float(string='Max Percentage for Total Loans Per Department',
    related='company_id.max_department', readonly=False)
    max_employee = fields.Float(string='Max Percentage for Total Loans Per Employee',
    related='company_id.max_employee' , readonly=False)



    

