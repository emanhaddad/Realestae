# -*- coding: utf-8 -*-

from odoo import api, fields, models, _
from dateutil import relativedelta


class HrEmployeeViolation(models.Model):
    _name = 'hr.employee.violation'
    _description = 'Employee Violation'

    name = fields.Char('Name', default=lambda self: _('New'))
    employee_id = fields.Many2one('hr.employee', 'Employee')
    violation_id = fields.Many2one('hr.violation', 'Violation')
    violation_date = fields.Date('Violation Date')
    description = fields.Text('Description')
    penalty_start_date = fields.Date('Penalty Start Date')
    penalty_id = fields.Many2one('hr.penalty', 'Penalty')
    amount_type = fields.Selection([('amount', 'Amount'),('percent', 'Percentage')], string="Calculation Type")
    percentage = fields.Integer('Percentage')
    amount = fields.Integer('Amount')
    penalty_committee = fields.Many2many('hr.employee', string='Penalty Committee')
    state = fields.Selection([('draft', 'Draft'),('in_progress', 'IN Progress'),('done', 'Done')], string='State', default='draft')

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date' in vals and vals['date']:
                seq_date = vals['date']
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.employee.violation', sequence_date=seq_date) or _('New')

        result = super(HrEmployeeViolation, self).create(vals)
        
        return result
    
    def confirm(self) :
        for rec in self :
            rec.write({'state' : 'in_progress'})

    def calculate(self) :
        for rec in self :
            if rec.amount or rec.percentage :
                if rec.amount_type == 'amount' :
                    amount = rec.amount
                if rec.amount_type == 'percent' :
                    amount = 0.0
                    for rule in rec.penalty_id.salary_rule_ids :
                        amount += rule.compute_allowed_deduct_amount(rec.employee_id.contract_id)
                    amount = amount*rec.percentage /100
                if rec.violation_id.has_penalty == True and rec.penalty_id.salary_rule_id :
                    exception_id = self.env['hr.salary.exception'].create({
                            'employee_id': rec.employee_id.id,
                            'contract_id':rec.employee_id.contract_id.id,
                            'exception_type': 'allocation',
                            'salary_rule_id': rec.penalty_id.salary_rule_id.id,
                            'date_from':rec.penalty_start_date,
                            'date_to':fields.Date.from_string(rec.penalty_start_date) + relativedelta.relativedelta(months=+1),
                            'amount': amount,
                        })
            
            rec.write({'state' : 'done'})