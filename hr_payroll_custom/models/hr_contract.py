# -*- coding:utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models

class Salaryexceptions(models.Model):
    _name = 'hr.salary.exception'
    _description = 'Salary exception'
    _inherit = ['mail.thread']

    name = fields.Char(readonly=True, default="New", string='Reference')
    contract_id = fields.Many2one('hr.contract', string='Contract', track_visibility='onchange', required=True)
    employee_id = fields.Many2one('hr.employee', string='Employee', required=True, track_visibility='onchange')
    exception_type = fields.Selection([
        ('allocation', 'Allocation'),
        ('exclude', 'Exclude')], 'exception Type', track_visibility='always', required=True)
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule', track_visibility='onchange', required=True)
    amount = fields.Float(string='Amount', required=True, )
    date_from = fields.Date(string='From Date', required=True, )
    date_to = fields.Date(string='To Date')
    payslip_id = fields.Many2one('hr.payslip')
    active = fields.Boolean(string='Is Active', default=True)

class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    salary_exception_ids = fields.One2many('hr.salary.exception', 'payslip_id')  

    def compute_sheet(self):
        for rec in self :	
            clause = [
            ('date_to', '<=', rec.date_to), 
            ('date_from', '>=', rec.date_from),
            ('employee_id', '=', rec.employee_id.id),
        ]
        
            salary_exception_ids = self.env['hr.salary.exception'].search(clause)

            rec.salary_exception_ids = salary_exception_ids
        super(HrPayslip, self).compute_sheet()  
