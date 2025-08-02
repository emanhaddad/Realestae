# -*- coding: utf-8 -*-
##############################################################################
#       App-script Business Solutions
#
##############################################################################

from odoo import fields, models, api, exceptions, _
import time
from datetime import datetime
from odoo.exceptions import ValidationError ,UserError
from dateutil import relativedelta
import math
import logging
_logger = logging.getLogger(__name__)

class RealBookingCancellationWiz(models.TransientModel):
    _name = "real.booking.cancellation"
    
    booking_id = fields.Many2one('real.estate.booking', string='Real estate Booking', readonly=True,store=True)
    reason_id = fields.Many2one('booking.cancel.reason', string="Cancellation reason",required=True)
    date = fields.Date(
        string=' Date',
        index=True,
    )
   

    def approve_cancellation(self):  
        _logger.info('KKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKKK inside cancel method')
        if self.booking_id:
            # if self.reason_id.return_payment:
                # last_cash_order = self.env['cash.order'].search([], order='id desc', limit=1)
                # if last_cash_order:
                #     last_sequence = int(last_cash_order.name.split('/')[-1])
                # else:
                #     last_sequence = 0
                # new_sequence = last_sequence + 1
                # new_cash_order_name = f'CP/{new_sequence:02d}'
                # payment = self.env['account.payment'].sudo().create({
                #     'partner_id':self.booking_id.partner_id.id,
                #     'journal_id':self.booking_id.journal_id.id,
                #     'payment_type':'outbound',
                #     'cost_center':self.booking_id.cost_center.id,
                #     'date':self.date,
                #     'ref':self.booking_id.name,
                #     'amount':c,
                #     'ref': ('Cancel booking of unit: '+ self.booking_id.unit_id.unit_name) })
                

                # payment_id.action_finance() 
                # self.booking_id.payment_ids = [(4,payment.id)]
            self.booking_id.write({'cancel_reason_id': self.reason_id.id,'state':'cancel'})
            self.booking_id.unit_id.write({'state':'available'})
            _logger.info('********************************************************** return payment?')
            _logger.info(self.reason_id.return_payment)
            _logger.info(self.reason_id)
            
            
            """
            new_entry_id = self.env['account.move'].create({
            'partner_id':self.partner_id.id,
            'invoice_date': fields.Date.today(),
            'move_type':'entry',
            'journal_id': self.booking_id.journal_id.id,
            'line_ids':
            [(0, None, {
                        'name': 'Cancel Booking' +  self.booking_id.name or '',
                        #'price_unit':  self.amount,
                        #'quantity': 1.0,
                        'account_id': self.booking_id.account_id.id,
                        'partner_id': self.booking_id.partner_id.id,
                        'analytic_account_id':self.booking_id.real_estate_id.analytic_id.id,
                        'debit':self.booking_id.amount,
                    }),
            (0, None, {
                        'name': 'Booking' +  self.booking_id.name or '',
                        #'price_unit':  self.amount,
                        #'quantity': 1.0,
                        'account_id': self.booking_id.journal_id.default_account_id.id,
                        'partner_id': self.booking_id.partner_id.id,
                        'analytic_account_id':False,
                        'credit':self.booking_id.amount,
                    }),
            ]
            })
            if new_entry_id:
                self.booking_id.entry_ids=[(4,new_entry_id.id)]
            """
            #if self.reason_id.return_payment:
            #   reverse=self.env['account.move.reversal'].sudo().create({'refund_method':'cancel',
            #       'reason':self.reason_id.name,
            #       'move_ids': [(4,self.booking_id.invoice_id.id)]})
            #   _logger.info('**********************************************************')
            #   _logger.info(reverse)
            #   reverse.reverse_moves()

            return True

    