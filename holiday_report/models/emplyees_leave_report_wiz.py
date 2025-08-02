# -*- coding: utf-8 -*-
import time
from datetime import datetime,timedelta
from dateutil.relativedelta import relativedelta
from datetime import time as datetime_time
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT as DATE_FORMAT,DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
from odoo import api,fields,models,_
from dateutil import relativedelta


class employeesLeavesReport(models.TransientModel):
	_name= "leaves.report.wiz"

	department_ids = fields.Many2many('hr.department','rel_leave_dpartment','leave_id','department_id',string='Department')
	holiday_status_ids = fields.Many2many("hr.leave.type",string="Holiday Type")
	employee_ids = fields.Many2many('hr.employee',string="Employees")
	report_type = fields.Selection([('leave','Time Off'),('permission','Permissions'),('planned','Planned')],default='leave',string="Report For")

	from_date = fields.Date(default=time.strftime('%Y-%m-01'),string="From Date")
	to_date = fields.Date(default=str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],string="To Date")


	def get_report(self):
		data={
		'ids':self.id,
		'model':self._name,
		'form': {
		'department_ids':self.department_ids.ids,
		'holiday_status_ids': self.holiday_status_ids.ids,
		'employee_ids' : self.employee_ids.ids,
		'report_type': self.report_type,
		'from_date': self.from_date,
		'to_date' : self.to_date,

		}
		}
		return self.env.ref('holiday_report.employee_leaves_report').report_action(self,data=data)


class reportEmployeesLeaves(models.AbstractModel):
	_name ='report.holiday_report.employee_leaves_report_template'


	@api.model
	def _get_report_values(self, docids, data=None):
		department_ids = data['form']['department_ids']
		holiday_status_ids = data['form']['holiday_status_ids']
		employee_ids = data['form']['employee_ids']
		report_type = data['form']['report_type']
		from_date = data['form']['from_date']
		to_date = data['form']['to_date']

		docs=[]
		docd = []
		domain = []
		ty_request_unit = ''

		if report_type == 'leave':
			domain.append(('request_date_from','>=', from_date))
			domain.append(('request_date_to','<=',to_date))
			domain.append(('holiday_status_id.request_unit', '=', 'day'))
			domain.append(('state','in', ['validate1','validate']))
		
		elif report_type == 'permission':
			domain.append(('request_date_from','>=', from_date))
			domain.append(('request_date_from','<=',to_date))
			domain.append(('holiday_status_id.request_unit', '!=', 'day'))
			domain.append(('state','in', ['validate1','validate']))

		elif report_type == 'planned':
			domain.append(('request_date_from','>=', from_date))
			domain.append(('request_date_to','<=',to_date))
			domain.append(('holiday_status_id.request_unit', '=', 'day'))
			domain.append(('state','=', 'draft'))
		

		if holiday_status_ids:
			domain.append(('holiday_status_id', 'in', holiday_status_ids))
			

		if department_ids:
			domain.append(('department_id', 'in', department_ids))
			

		if employee_ids:
			domain.append(('employee_id', 'in', employee_ids))
			

		leaves = self.env['hr.leave'].search(domain)


		for l in leaves:

			hfrom = ""
			hto = ""


			ty_request_unit = l.holiday_status_id.request_unit,

			if l.request_hour_from == '0':
				hfrom = '12:00 ص'
			elif l.request_hour_from == '1':
				hfrom = '1:00 ص'
			elif l.request_hour_from == '2':
				hfrom = '2:00 ص'
			elif l.request_hour_from == '3':
				hfrom = '3:00 ص'
			elif l.request_hour_from == '4':
				hfrom = '4:00 ص'
			elif l.request_hour_from == '5':
				hfrom = '5:00 ص'
			elif l.request_hour_from == '6':
				hfrom = '6:00 ص'
			elif l.request_hour_from == '7':
				hfrom = '7:00 ص'
			elif l.request_hour_from == '8':
				hfrom = '8:00 ص'
			elif l.request_hour_from == '9':
				hfrom = '9:00 ص'
			elif l.request_hour_from == '10':
				hfrom = '10:00 ص'
			elif l.request_hour_from == '11':
				hfrom = '11:00 ص'
			elif l.request_hour_from == '12':
				hfrom = '12:00 م'
			elif l.request_hour_from == '13':
				hfrom = '1:00 م'
			elif l.request_hour_from == '14':
				hfrom = '2:00 م'
			elif l.request_hour_from == '15':
				hfrom = '3:00 م'
			elif l.request_hour_from == '16':
				hfrom = '4:00 م'
			elif l.request_hour_from == '17':
				hfrom = '5:00 م'
			elif l.request_hour_from == '18':
				hfrom = '6:00 م'
			elif l.request_hour_from == '19':
				hfrom = '7:00 م'
			elif l.request_hour_from == '20':
				hfrom = '8:00 م'
			elif l.request_hour_from == '21':
				hfrom = '9:00 م'
			elif l.request_hour_from == '22':
				hfrom = '10:00 م'
			elif l.request_hour_from == '23':
				hfrom = '11:00 م'

			elif l.request_hour_from == '0.5':
				hfrom = '12:30 ص'
			elif l.request_hour_from == '1.5':
				hfrom = '1:30 ص'
			elif l.request_hour_from == '2.5':
				hfrom = '2:30 ص'
			elif l.request_hour_from == '3.5':
				hfrom = '3:30 ص'
			elif l.request_hour_from == '4.5':
				hfrom = '4:30 ص'
			elif l.request_hour_from == '5.5':
				hfrom = '5:30 ص'
			elif l.request_hour_from == '6.5':
				hfrom = '6:30 ص'
			elif l.request_hour_from == '7.5':
				hfrom = '7:30 ص'
			elif l.request_hour_from == '8.5':
				hfrom = '8:30 ص'
			elif l.request_hour_from == '9.5':
				hfrom = '9:30 ص'
			elif l.request_hour_from == '10.5':
				hfrom = '10:30 ص'
			elif l.request_hour_from == '11.5':
				hfrom = '11:30 ص'
			elif l.request_hour_from == '12.5':
				hfrom = '12:30 م'
			elif l.request_hour_from == '13.5':
				hfrom = '1:30 م'
			elif l.request_hour_from == '14.5':
				hfrom = '2:30 م'
			elif l.request_hour_from == '15.5':
				hfrom = '3:30 م'
			elif l.request_hour_from == '16.5':
				hfrom = '4:30 م'
			elif l.request_hour_from == '17.5':
				hfrom = '5:30 م'
			elif l.request_hour_from == '18.5':
				hfrom = '6:30 م'
			elif l.request_hour_from == '19.5':
				hfrom = '7:30 م'
			elif l.request_hour_from == '20.5':
				hfrom = '8:30 م'
			elif l.request_hour_from == '21.5':
				hfrom = '9:30 م'
			elif l.request_hour_from == '22.5':
				hfrom = '10:30 م'
			elif l.request_hour_from == '23.5':
				hfrom = '11:30 م'

		# HOURS TO 

			if l.request_hour_to == '0':
				hto = '12:00 ص'
			elif l.request_hour_to == '1':
				hto = '1:00 ص'
			elif l.request_hour_to == '2':
				hto = '2:00 ص'
			elif l.request_hour_to == '3':
				hto = '3:00 ص'
			elif l.request_hour_to == '4':
				hto = '4:00 ص'
			elif l.request_hour_to == '5':
				hto = '5:00 ص'
			elif l.request_hour_to == '6':
				hto = '6:00 ص'
			elif l.request_hour_to == '7':
				hto = '7:00 ص'
			elif l.request_hour_to == '8':
				hto = '8:00 ص'
			elif l.request_hour_to == '9':
				hto = '9:00 ص'
			elif l.request_hour_to == '10':
				hto = '10:00 ص'
			elif l.request_hour_to == '11':
				hto = '11:00 ص'
			elif l.request_hour_to == '12':
				hto = '12:00 م'
			elif l.request_hour_to == '13':
				hto = '1:00 م'
			elif l.request_hour_to == '14':
				hto = '2:00 م'
			elif l.request_hour_to == '15':
				hto = '3:00 م'
			elif l.request_hour_to == '16':
				hto = '4:00 م'
			elif l.request_hour_to == '17':
				hto = '5:00 م'
			elif l.request_hour_to == '18':
				hto = '6:00 م'
			elif l.request_hour_to == '19':
				hto = '7:00 م'
			elif l.request_hour_to == '20':
				hto = '8:00 م'
			elif l.request_hour_to == '21':
				hto = '9:00 م'
			elif l.request_hour_to == '22':
				hto = '10:00 م'
			elif l.request_hour_to == '23':
				hto = '11:00 م'

			elif l.request_hour_to == '0.5':
				hto = '12:30 ص'
			elif l.request_hour_to == '1.5':
				hto = '1:30 ص'
			elif l.request_hour_to == '2.5':
				hto = '2:30 ص'
			elif l.request_hour_to == '3.5':
				hto = '3:30 ص'
			elif l.request_hour_to == '4.5':
				hto = '4:30 ص'
			elif l.request_hour_to == '5.5':
				hto = '5:30 ص'
			elif l.request_hour_to == '6.5':
				hto = '6:30 ص'
			elif l.request_hour_to == '7.5':
				hto = '7:30 ص'
			elif l.request_hour_to == '8.5':
				hto = '8:30 ص'
			elif l.request_hour_to == '9.5':
				hto = '9:30 ص'
			elif l.request_hour_to == '10.5':
				hto = '10:30 ص'
			elif l.request_hour_to == '11.5':
				hto = '11:30 ص'
			elif l.request_hour_to == '12.5':
				hto = '12:30 م'
			elif l.request_hour_to == '13.5':
				hto = '1:30 م'
			elif l.request_hour_to == '14.5':
				hto = '2:30 م'
			elif l.request_hour_to == '15.5':
				hto = '3:30 م'
			elif l.request_hour_to == '16.5':
				hto = '4:30 م'
			elif l.request_hour_to == '17.5':
				hto = '5:30 م'
			elif l.request_hour_to == '18.5':
				hto = '6:30 م'
			elif l.request_hour_to == '19.5':
				hto = '7:30 م'
			elif l.request_hour_to == '20.5':
				hto = '8:30 م'
			elif l.request_hour_to == '21.5':
				hto = '9:30 م'
			elif l.request_hour_to == '22.5':
				hto = '10:30 م'
			elif l.request_hour_to == '23.5':
				hto = '11:30 م'

		
			if l.employee_id:
			
				docs.append({
					'code':l.employee_id.barcode,
					'name':l.employee_id.name,
					'department':l.department_id.name,
					'holiday_status':l.holiday_status_id.name,
					'holiday_type': l.holiday_type,
					'day_duration':l.number_of_days_display,
					'hours_duration':l.number_of_hours_display,
					'request_hour_from': hfrom,
					'request_hour_to': hto,
					'request_date_from': l.request_date_from,
					'request_date_to': l.request_date_to,
					'request_unit_hours': l.request_unit_hours,
					'repo_type': l.holiday_status_id.request_unit,
					})



		return {
		'doc_model': 'hr.employee',
		'doc_ids': data['ids'],
		'doc_model': data['model'],
		'docsw': docs,
		'report_type':report_type,
		'ty_request_unit': ty_request_unit,
		# 'docd':docd,
		'doc': self,
		}
