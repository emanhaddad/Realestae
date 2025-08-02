# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools.translate import _


class ReturnExpiredContract(models.Model):
    _name = 're.expired.contract'

    name = fields.Char(compute="name_compute",store=True)
    start_date = fields.Date('Start Date')
    end_date = fields.Date('End Date')
    expired_lines = fields.One2many('expired.lines.model','return_c_id',string="Expired Contracts")
    has_lines = fields.Boolean(string="Has Lines")
    state = fields.Selection([('draft','Draft'),('confirmed','Confirmed'),('done','Done')],default="draft")
    date = fields.Date('Date', default=fields.Date.today())

    @api.depends('start_date' , 'end_date')
    def name_compute(self):
        if self.start_date and self.end_date:
            self.name = fields.Date.to_string(self.start_date) +","+fields.Date.to_string(self.end_date)

    def confirm_return(self):
        if self.has_lines != True:
            raise ValidationError(
                        _("You mus has a least one contract"))
        for rec in self.expired_lines:
            if rec.return_boolean == True:
                if not rec.new_start_date:
                    raise ValidationError(
                        _("You must specify new start date") )

                if not rec.new_end_date:
                    raise ValidationError(
                        _("You must specify new end date") )

                if rec.new_end_date and self.date:
                    if rec.new_end_date <= self.date:
                        raise ValidationError(_("New end date is after today and this contract is expired") )

                    if rec.new_start_date < self.date:
                        raise ValidationError(_("New start date is after today or equal today") )

                    if rec.new_start_date > rec.new_end_date:
                        raise ValidationError(_("New start date cannot be after new end date") )

        self.write({'state':'confirmed'})

    def get_expired_contracts(self):
        contracts = self.env['realestate.contract.model'].search([('date_end','>=',self.start_date),('date_end','<=',self.end_date),('state','=','expired')])
        if contracts:
            for c in contracts:
                self.expired_lines.create({
                    'return_c_id':self.id,
                    'contract_id':c.id,
                    })
            self.has_lines = True

        else:
            raise ValidationError(
                    _("There is no expired Contracts") )

    def return_expired_contracts(self):
        for rec in self.expired_lines:
            if rec.return_boolean == True:
                rec.contract_id.state = 'valid'

                if rec.new_start_date:
                    rec.contract_id.date_start = rec.new_start_date
                
               
                if rec.new_end_date:
                    rec.contract_id.date_end = rec.new_end_date

                if rec.new_amount:
                    rec.contract_id.contract_amount = rec.new_amount
                else:
                    rec.contract_id.contract_amount = rec.old_amount
                    rec.new_amount = rec.old_amount


                if rec.new_pay_duration:
                    rec.contract_id.cost_duration = rec.new_pay_duration
                else:
                    rec.contract_id.cost_duration = rec.old_cost_duration
                    rec.new_pay_duration = rec.old_cost_duration

                self.write({'state':'done'})

                
class ExpiredLines(models.Model):
    _name = 'expired.lines.model'

    return_c_id = fields.Many2one('re.expired.contract')
    return_boolean = fields.Boolean(string="Return",default=True)
    contract_id = fields.Many2one('realestate.contract.model',string="Contract")
    unit_id = fields.Many2one(related="contract_id.unit_id",string="Unit",store=True)
    renter_id = fields.Many2one(related="contract_id.partner_id",string="Renter",store=True)
    date = fields.Date(related="contract_id.date")
    old_amount = fields.Monetary(related="contract_id.contract_amount",store=True)
    old_cost_duration = fields.Selection(related="contract_id.cost_duration",store=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", oldname='currency')
    new_start_date = fields.Date(string="New Start Date")
    new_end_date  = fields.Date(string="New End Date")
    new_amount = fields.Monetary(string="New Amount")
    new_pay_duration = fields.Selection([
         ('monthly', 'Month(s)'),
         ('yearly', 'Year(s)'),
         ])

    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", oldname='currency')
