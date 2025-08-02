from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api ,_
from datetime import datetime, timedelta


class real_estate_units(models.Model):
    _inherit = "real.estate.units"
    

    contract_id = fields.Many2one('realestate.contract.model', string="Rent Contract")
    image_ids = fields.One2many('product.images','product_id',
        #related="product_id.image_ids",
        string='Product Images')
    
    '''
    @api.model
    def create(self, values):
        # Override the original create function for the real.estate.units model
        if values.get('unit_name') is None :
           values.update({'unit_name':values.get('code')})
        record = super(real_estate_units, self).create(values)       
        return record
    
    @api.constrains('rent_amount')
    def rent_amount_validation(self):
        if self.rent_amount <= 0.0 :
            raise ValidationError(_('Rent Amount cannot be zero or less'))

    @api.onchange('renter_id')
    def no_charss(self):
        partner_id = self.env['res.partner'].search([('name','=',self.renter_id.name)])
        partner_id.write({
            'unit_name':self.renter_id.name,
            'unit_code':self.code
        })


    '''