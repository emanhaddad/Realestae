from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api ,_
from datetime import datetime, timedelta


class BookingCancelReason(models.Model):
    _name = "booking.cancel.reason"


    name = fields.Char(string='Name',index=True)
    return_payment = fields.Boolean('Return payment')