from odoo import api, fields, models

class account_voichere(models.Model):
	_inherit = ['account.voucher']
	
	cash_order_id = fields.Many2one("cash.order" , string="Cash Order")
	