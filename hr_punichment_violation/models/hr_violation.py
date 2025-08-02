# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrViolation(models.Model):
    _name = 'hr.violation'
    _description = 'HR Violation'

    name = fields.Char('Name', required=True)
    category = fields.Selection([
        ('attendance','Attendance'),
        ('org','Organization'),
        ('behavior','Behavior'),
        ], string='Category')
    has_penalty = fields.Boolean('Has Penalty')
    active = fields.Boolean('Active', default=True)