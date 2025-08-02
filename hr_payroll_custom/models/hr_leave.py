# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class hr_leave_type(models.Model):
    _inherit = 'hr.leave.type'

    rule_id = fields.Many2one("hr.salary.rule", "Rule")

