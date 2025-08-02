# -*- coding: utf-8 -*-

from odoo import api, fields, models, _


class HrPenalty(models.Model):
    _name = 'hr.penalty'
    _description = 'Employee penalty'
    _rec_name = 'violation_id'

    violation_id = fields.Many2one('hr.violation', string="Violation", required=True,ondelete='restrict')
    violation_category = fields.Selection([
        ('warning','Warning'),
        ('payment','Payment'),
        ('denail_of_bonus','Denail of bonus'),
        ('appraisal_postponing','Appraisal Postponing'),
        ('suspension','Suspension'),
        ('dismiss','Dismissal from work')
        ], string='Violation Category')
    first = fields.Selection([
        ('warning','Warning'),
        ('payroll_percentage','Payroll Percentage'),
        ('payroll_days','Payroll Days'),
        ('payroll_time','Payroll Time'),
        ('denail_of_bonus','Denail of bonus'),
        ('suspension_with_payment','Suspension with payment'),
        ('suspension_no_payment','Suspension without payment'),
        ], string='First Punichment')
    first_percentage = fields.Float("First Percentage")
    first_days = fields.Float("First Days")
    first_time = fields.Float("First Time")
    second = fields.Selection([
        ('warning','Warning'),
        ('payroll_percentage','Payroll Percentage'),
        ('payroll_days','Payroll Days'),
        ('payroll_time','Payroll Time'),
        ('denail_of_bonus','Denail of bonus'),
        ('suspension_with_payment','Suspension with payment'),
        ('suspension_no_payment','Suspension without payment'),
        ], string='Second Punichment')
    second_percentage = fields.Float("Second Percentage")
    second_days = fields.Float("Second Days")
    second_time = fields.Float("Second Time")
    third = fields.Selection([
        ('warning','Warning'),
        ('payroll_percentage','Payroll Percentage'),
        ('payroll_days','Payroll Days'),
        ('payroll_time','Payroll Time'),
        ('denail_of_bonus','Denail of bonus'),
        ('suspension_with_payment','Suspension with payment'),
        ('suspension_no_payment','Suspension without payment'),
        ], string='Third Punichment')
    third_percentage = fields.Float("Third Percentage")
    third_days = fields.Float("Third Days")
    third_time = fields.Float("Third Time")
    fourth = fields.Selection([
        ('warning','Warning'),
        ('payroll_percentage','Payroll Percentage'),
        ('payroll_days','Payroll Days'),
        ('payroll_time','Payroll Time'),
        ('denail_of_bonus','Denail of bonus'),
        ('suspension_with_payment','Suspension with payment'),
        ('suspension_no_payment','Suspension without payment'),
        ], string='Fourth Punichment')
    fourth_percentage = fields.Float("Fourth Percentage")
    fourth_days = fields.Float("Fourth Days")
    fourth_time = fields.Float("Fourth Time")
    salary_rule_id = fields.Many2one('hr.salary.rule', 'Rule')
    amount_type = fields.Selection([('amount', 'Fix Amount'),('percent', 'Based on salary')], string="Amount Type")
    salary_rule_ids = fields.Many2many('hr.salary.rule', string='Rules')

