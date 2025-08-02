from odoo import models, fields, api ,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class real_estate(models.Model):
    _inherit = "real.estate"

    
    income_amount= fields.Float(string="Annual Revenue",compute='_compute_income_amount',store = True)
    contract_id = fields.Many2one('realestate.contract.model', string=" Contract")
    image_ids = fields.One2many('product.images','product_id',
        #related="product_id.image_ids",
        string='Product Images')
    '''
    @api.model
    def create(self, values):
        # Override the original create function for the real.estate model
        if values.get('name') is None :
           values.update({'name':values.get('code')})
        record = super(real_estate, self).create(values)
        record['product_id'] = self.env["product.product"].sudo().create({
            'name':values.get('code') + " " + "Property",
            'list_price':values.get('rent_amount'),
            'standard_price':values.get('rent_amount'),
            'rent_ok':True,
            'type':'service',
            'categ_id':1,
        }).id
       
        return record
    

    @api.constrains('rent_amount')
    def rent_amount_validation(self):
        if self.rent_amount <= 0.0 :
            raise ValidationError(_('Rent Amount cannot be zero or less'))


    @api.depends('unit_ids')
    def _compute_income_amount(self):
        amount = 0.0
        for rec in self:
            if rec.unit_ids:
               for line in rec.unit_ids:
                   amount += line.rent_amount
            rec.income_amount = amount
    '''





   
