# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from datetime import datetime

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    annual_leave_days = fields.Integer(compute="_compute_annual_leave_counters", string="Annual Leave Days")
    annual_leave_total_days = fields.Integer(compute="_compute_annual_leave_counters", string="Annual Leave Total Days")
    annual_leave_available_days = fields.Integer(compute="_compute_annual_leave_counters", string="Annual Leave Available Days")
    special_leave_start_date = fields.Date(
        string='Special Leave Start Date'
    )
    special_leave_end_date = fields.Date(
        string='Special Leave End Date'
    )
    special_leave_days = fields.Integer(
        string='Special Leave Days',
        compute='calculate_special_leave_days'
    )
    

    @api.depends('special_leave_start_date','special_leave_end_date')
    def calculate_special_leave_days(self):
        for rec in self:
            rec.special_leave_days = 0
            if rec.special_leave_end_date and rec.special_leave_start_date:
                rec.special_leave_days = (rec.special_leave_end_date - rec.special_leave_start_date).days


    @api.onchange('special_leave_start_date','special_leave_end_date')
    def _onchange_special_leave_dates(self):
        if self.special_leave_end_date and self.special_leave_start_date:
            if self.special_leave_start_date > self.special_leave_end_date:
                raise ValidationError (_("special leave start date must not be greater than special leave end date"))


    @api.depends('start_date')
    def _compute_annual_leave_counters(self):
        for rec in self:
            annual_leave_days = 0.0
            annual_leave_total_days = 0.0
            emp_working_days = 0
            if self.start_date:
                emp_working_days = self.get_employee_working_days()

            emp_leave_request_ids = self.env['hr.leave'].search([('employee_id','=',self.id)])

            for leave in emp_leave_request_ids:
                if leave.holiday_status_id.is_annual_leave == True:
                    annual_leave_days += leave.number_of_days
            if emp_working_days > (365*5):
                annual_leave_total_days += (21*5)+self.calculate_annual_leave_v2(emp_working_days-(365*5))
            else:
                annual_leave_total_days += self.calculate_annual_leave_v1(emp_working_days)

            if annual_leave_days > 0:
                rec.annual_leave_days = annual_leave_days
            else:
                rec.annual_leave_days = 0
            if annual_leave_total_days > 0:
                rec.annual_leave_total_days = annual_leave_total_days
            else:
                rec.annual_leave_total_days = 0
            if annual_leave_total_days-annual_leave_days > 0:
                rec.annual_leave_available_days = annual_leave_total_days-annual_leave_days
            else:
                rec.annual_leave_available_days = 0

    def get_employee_working_days(self):
        current_date = fields.date.today()
        emp_working_days = (current_date-self.start_date).days
        return emp_working_days

    def calculate_annual_leave_v1(self,days):
        '''
            function to calculate annual leave days for employee who worked for less than 5 years
        '''
        leave_days = 21/365*days
        return leave_days

    def calculate_annual_leave_v2(self,days):
        '''
            function to calculate annual leave days for employee who worked for more than 5 years
        '''
        leave_days = 30/365*days
        return leave_days

    def view_emp_annual_leave_days(self):
        emp_leave_request_ids = self.env['hr.leave'].search([('employee_id','=',self.id)])
        ids_list = []

        for leave in emp_leave_request_ids:
            if leave.holiday_status_id.is_annual_leave == True:
                ids_list.append(leave.id)

        return {
            'name': _('Leave'),
            'view_mode': 'tree,form',
            'res_model': 'hr.leave',
            'view_id': False,
            'type': 'ir.actions.act_window',
            'domain': [('id','in',ids_list)],
        }


