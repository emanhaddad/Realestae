# -*- coding: utf-8 -*-
##############################################################################
#		App-script Business Solutions
#
##############################################################################

from odoo import fields, models, api, exceptions, _
import time
from datetime import datetime
from odoo.exceptions import ValidationError ,UserError
from dateutil import relativedelta
import math

class RealBookingCancellationWiz(models.TransientModel):
	_name = "real.booking.cancellation"
	
	booking_id = fields.Many2one('real.estate.booking', string='Real estate Booking', readonly=True,store=True)
	reason_id = fields.Many2one('booking.cancel.reason', string="Cancellation reason",required=True)

	

	def approve_cancellation(self):		
		if self.booking_id:
			self.booking_id.write({'cancel_reason_id': self.reason_id.id,'state':'cancel'})
			self.booking_id.unit_id.write({'state':'available'})
		return True

	