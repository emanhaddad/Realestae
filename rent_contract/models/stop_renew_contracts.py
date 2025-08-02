# -*- coding: utf-8 -*-

from odoo import models, fields, api

class StopContractsRenewal(models.Model):
    _name = 'stop.contracts.renewal'

    stop_date = fields.Date(string="Date of stop",default=fields.Date.context_today)
    line_ids = fields.One2many('realestate.contract.model','stop_id',string="Contract Lines")
    
    def stop_renewal_method(self):
        '''Confirm stop contract renew'''
        for rec in self.line_ids:
        	rec.auto_renewal = False
        	rec.stop_renew_date = self.stop_date
