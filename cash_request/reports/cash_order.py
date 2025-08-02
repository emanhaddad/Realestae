from odoo import api , models
from odoo import api, fields, models, _

class CashOrderReport(models.Model):
	_name = "report.cash_request.cash_order"



	@api.multi
	def render_hml(self,data=None):
		print '.............................. self is : ',self
		report_obj = self.env['report']
		report = report_obj._get_report_from_name('cash_request.cash_order_report')
		docargs = {
			'doc_ids' : self.ids ,
			'doc_model' : report.model ,
			'docs' : self,
		}

		return report_obj.render('cash_request.cash_order_report' , docargs)