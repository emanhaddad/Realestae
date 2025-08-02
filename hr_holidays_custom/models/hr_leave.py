# -*- encoding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError

class HolidaysType(models.Model):
    _inherit = 'hr.leave.type'

    is_annual_leave = fields.Boolean(string="Is Annual Leave")
    buy_leave = fields.Boolean(string="Buy Leave?")
    rule_ids = fields.Many2many("hr.salary.rule", string="Rules")

    @api.onchange('is_annual_leave')
    def _onchange_is_annual_leave(self):
        annual_leave_count = self.env['hr.leave.type'].search_count([('is_annual_leave','=',True)])
        if annual_leave_count >= 1 and self.is_annual_leave == True:
            raise ValidationError(_('Unable to set more than one leave type as Annual Leave'))

    def get_employees_days(self, employee_ids):
        for rec in self :
            if not rec.buy_leave :
                return super(HolidaysType, rec).get_employees_days(employee_ids)
            else :
                result = {
		        employee_id: {
		            leave_type.id: {
		                'max_leaves': 0,
		                'leaves_taken': 0,
		                'remaining_leaves': 0,
		                'virtual_remaining_leaves': 0,
		                'virtual_leaves_taken': 0,
		            } for leave_type in rec
		        } for employee_id in employee_ids
		    }

                buy_leaves = self.env['hr.bonus'].search([
		        ('employee_id', 'in', employee_ids),
		        ('state', '=','paid'),
		        ('leave_type_id', 'in', rec.ids)
		    ])
                allocations = self.env['hr.leave.allocation'].search([
            ('employee_id', 'in', employee_ids),
            ('state', 'in', ['confirm', 'validate1', 'validate']),
            ('holiday_status_id', 'in', rec.ids)
        ])
                print (buy_leaves,"HHHHHHHHHHHHHHHHHHHHHHHHHhh")
                for buy_leave in buy_leaves:
                    status_dict = result[buy_leave.employee_id.id][buy_leave.leave_type_id.id]
                    status_dict['virtual_remaining_leaves'] -= (buy_leave.number_of_days)
                    status_dict['remaining_leaves'] -= (buy_leave.number_of_days)
                for allocation in allocations.sudo():
                    status_dict = result[allocation.employee_id.id][allocation.holiday_status_id.id]
                    if allocation.state == 'validate':
                        # note: add only validated allocation even for the virtual
                        # count; otherwise pending then refused allocation allow
                        # the employee to create more leaves than possible
                        status_dict['virtual_remaining_leaves'] += (allocation.number_of_hours_display
                                                          if allocation.type_request_unit == 'hour'
                                                          else allocation.number_of_days)
                        status_dict['max_leaves'] += (allocation.number_of_hours_display
                                            if allocation.type_request_unit == 'hour'
                                            else allocation.number_of_days)
                        status_dict['remaining_leaves'] += (allocation.number_of_hours_display
                                                  if allocation.type_request_unit == 'hour'
                                                  else allocation.number_of_days)
                return result

