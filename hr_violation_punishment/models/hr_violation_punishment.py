# -*- coding: utf-8 -*-
##############################################################################
#
#    
#    
#
##############################################################################

from odoo import api, fields, models, _
from datetime import date, datetime, timedelta
from odoo.exceptions import UserError, ValidationError
from dateutil import relativedelta
import calendar


class ViolationClasification(models.Model):
    _name = "hr.violation.clasification"
    _description = "Violations Clasification"

    name = fields.Char(string='Violation Clasification', required=True, copy=False)
    code = fields.Char(string='Code')

    _sql_constraints = [
       ('code_uniq', 'unique (code)', 'The code of the Violation clasification must be unique !'),
       ('name_uniqe', 'unique (name)', 'The name of the Violation clasification must be unique !'),
    ] 


class Punishment(models.Model):
    _name = "hr.punishment"
    _description = "Punishments"

    name = fields.Char(string='Name', required=True, copy=False)
    type = fields.Selection([
        ('warning','Warning'),
        ('penalty','Penalty'),
        ('dismiss','Dismiss'),
        ('deprivation','Deprivation')
        ], string='Punishment Type')
    reward = fields.Selection([
        ('with_reward','With Reward'),
        ('without_reward','Without Reward')
        ], string='Reward')
    dismiss_classification = fields.Many2one('hr.departure.reason', string='Dismiss Classification',ondelete='restrict')
    active = fields.Boolean(default=True)
    penalty_type = fields.Selection([
        ('fixed','Fixed Amount'),
        ('salary','Based on Salary')
        ], required=False, string='Penalty Type')
    penalty_amount_type = fields.Selection( string="Penalty Amount Computation", required=False,
        selection=[('days', 'Days'), ('percent', 'Percentage')], default='days')
    amount = fields.Float(string='Amount')
    days = fields.Integer(string='Days')
    percentage = fields.Float(string='Percentage')
    allow_deduct = fields.Many2one('hr.salary.rule', string='Allowance',ondelete='restrict')  
    deduct_id = fields.Many2one('hr.salary.rule', string='Deduction', domain=[('special','=',True)],ondelete='restrict')

    deduct_ids = fields.Many2many('hr.salary.rule', string='Deduction', domain=[('special','=',True)],ondelete='restrict')

    _sql_constraints = [
       ('name_uniqe', 'unique (name)', 'The name of the punishment must be unique !'),
    ] 

class Violation(models.Model):
    _name = "hr.violation"
    _description = "Violations"

    name = fields.Char(string='Violation Name', copy=False, required=True)
    violation_clasification_id = fields.Many2one('hr.violation.clasification', string='Violation Clasification', required=True,ondelete='restrict')
    active = fields.Boolean(default=True)
    has_punishment = fields.Boolean(string='Has Punishment', default=True)
    punishment_first_ids = fields.Many2many('hr.punishment', 'violation_punishment_rel_fir', 
       string='Punishment/First Time')
    punishment_second_ids= fields.Many2many('hr.punishment', 'violation_punishment_rel_sec',  
       string='Punishment/Second Time')
    punishment_third_ids = fields.Many2many('hr.punishment', 'violation_punishment_rel_thi',  
       string='Punishment/Third Time')
    punishment_fourth_ids = fields.Many2many('hr.punishment', 'violation_punishment_rel_fou',  
       string='Punishment/Fourth Time')

    _sql_constraints = [
       ('name_uniqe', 'unique (name)', 'The name of the Violation clasification must be unique !'),
    ] 


class ViolationPunishment(models.Model):
    _name = "hr.violation.punishment"
    _description = "Violations and Punishments"
    _inherit = ['mail.thread']
    _rec_name = "employee_id"
    _order = "violation_date Desc"

    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    violation_id = fields.Many2one('hr.violation', string="Violation", required=True,ondelete='restrict')
    violation_date = fields.Date('Violation Date', required=True)
    violation_descr = fields.Text(string='Violation Description')
    decision_descr = fields.Text(string="Decision Description")
    decision_date = fields.Date(string='Decision Date', required=True)
    penalty_amount = fields.Float(compute='_compute_penalty_amount',string="Penalty Amount")
    punishment_ids = fields.Many2many('hr.punishment', 'violation_punishment_rel',  
       string='Punishments')
    employee_ids = fields.Many2many('hr.employee',string='Employees')
    payslip_id = fields.Many2one('hr.payslip', string="Payslip Ref.", ondelete='set null')
    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirm', 'Waiting for Committee Decision'),
        ('close', 'Close')
    ], string='Status', readonly=True, tracking=True, default='draft')
    time = fields.Selection([
        ('first','First Time'),
        ('second','Second Time'),
        ('third','Third Time'),
        ('fourth','Fourth Time')
        ], string='Time', copy=False, default='first')
    employee_company_id = fields.Many2one(related='employee_id.company_id', readonly=True, store=True)
    percentage = fields.Float(string='Percentage')
    
    @api.depends('punishment_ids')
    def _compute_penalty_amount(self):
        penalty_amount = 0.0
        for rec in self:
            if rec.employee_id.contract_id:
                for pun in rec.punishment_ids:
                    if pun.type == 'penalty':
                        if pun.penalty_type == 'fixed':
                            penalty_amount += pun.amount
                        else:
                            amount, qty, rate = pun.allow_deduct._compute_rule({'contract':rec.employee_id.contract_id})
                            days = 30
                            amount = amount / days
                            if rec.percentage :
                                penalty_amount += amount * rec.percentage / 100
                            else :
                               if pun.penalty_amount_type == 'percent':
                                   penalty_amount += amount * pun.percentage / 100
                               else:
                                   penalty_amount += amount * pun.days

            rec.penalty_amount = penalty_amount

    @api.onchange('employee_id','violation_id','violation_date')
    def onchange_punishment(self):
        self.punishment_ids=False
        if self.employee_id and self.violation_id and self.violation_date:
            punishment=self.search([('employee_id','=',self.employee_id.id),('violation_id','=',self.violation_id.id),('id','!=',self._origin.id)],order='violation_date desc', limit=1)
            if punishment and punishment.violation_date.month == self.violation_date.month :
                if punishment.time == 'first' :
                    self.time = 'second'
                    self.punishment_ids = self.violation_id.punishment_second_ids
                elif punishment.time == 'second' :
                    self.time = 'third'
                    self.punishment_ids = self.violation_id.punishment_third_ids
                elif punishment.time == 'third' :
                    self.time = 'fourth'
                    self.punishment_ids = self.violation_id.punishment_fourth_ids
                else :
                    self.time = 'fourth'
                    self.punishment_ids = self.violation_id.punishment_fourth_ids

            else :
                    self.time = 'first'
                    self.punishment_ids = self.violation_id.punishment_first_ids
            '''if len(punishment) == 0:
                self.time = 'first'
                self.punishment_ids = self.violation_id.punishment_first_ids
            elif len(punishment) == 1:
                self.time = 'second'
                self.punishment_ids = self.violation_id.punishment_second_ids
            elif len(punishment) == 2:
                self.time = 'third'
                self.punishment_ids = self.violation_id.punishment_third_ids
            else:
                self.time = 'fourth'
                self.punishment_ids = self.violation_id.punishment_fourth_ids'''

    @api.constrains('time')
    def _check_punishment_time(self):
        for rec in self:
            punishment=self.search([('employee_id','=',rec.employee_id.id),('violation_id','=',rec.violation_id.id), ('violation_date','<=',rec.violation_date)])
            if rec.time == 'first':
                ttime = 1
            elif rec.time == 'second':
                ttime = 2
            elif rec.time == 'third':
                ttime = 3
            else:
                ttime = 4
            if ttime > len(punishment):
                raise UserError(_('Times an advanced system violation.'))

    @api.constrains('violation_date')
    def _compviolationdate(self):
        if self.violation_date > fields.Datetime.now().date():
            raise ValidationError('violation date cannot be after this date')
    
    def unlink(self):
        for punishment in self:
            if punishment.state != 'draft':
                raise UserError(_('Cannot delete record(s) which are not in draft state.'))
        return super(ViolationPunishment, self).unlink()

    def action_draft(self):
        self.write({'state': 'draft'})

    def action_confirm(self):
        self.write({'state': 'confirm'})

    def action_close(self):
        for punishment in self.punishment_ids:
            if self.penalty_amount > 0.0:
                if punishment.type == 'penalty' and punishment.deduct_ids:
                    for deduct_id in punishment.deduct_ids :
                        if self.employee_id.contract_id.structure_type_id.default_struct_id == deduct_id.struct_id :
                            deduct = deduct_id
                    exception_id = self.env['hr.salary.exception'].create({
                            'employee_id': self.employee_id.id,
                            'contract_id':self.employee_id.contract_id.id,
                            'exception_type': 'allocation',
                            'salary_rule_id':deduct.id,
                            'date_from':self.decision_date,
                            'date_to': self.decision_date.replace(day=calendar.monthrange(self.decision_date.year, self.decision_date.month)[1]),
                            'amount':self.penalty_amount,
                        })
        self.write({'state': 'close'})

    doc_count = fields.Integer(compute='_compute_attached_docs_count',
                               string="Number of documents attached")

    def _compute_attached_docs_count(self):

        Attachment = self.env['ir.attachment']

        for employee in self:
            employee.doc_count = Attachment.search_count([('res_model', '=',
                                                       'hr.employee'), ('res_id', '=', employee.id)])
