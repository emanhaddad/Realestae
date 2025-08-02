from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError
import re


class res_partner(models.Model):
    _inherit = 'res.partner'

    partner_type = fields.Selection([
        ('owner','Owner'),
        ('supervisor','Supervisor'),
        ('investor','Investor'),
        ('entrepreneur','Entrepreneur'),
        ('contractor','Contractor'),
        ('employee','Employee'),
        ('vendor','Vendor')], "Type")
    # id_partner_number = fields.Char(string='ID Number')
    partner_gender= fields.Selection([('male', 'Male'),('female','Female')], "Gender", tracking=True)
    date_birth = fields.Date('Birth Date', tracking=True)
    code=fields.Char('Code', tracking=True)
    unit_name = fields.Char('Unit', tracking=True)
    unit_code = fields.Char('code', tracking=True)
    unit_id = fields.Many2one('real.estate.units', string='Unit', tracking=True)
    unit_name = fields.Char(related='unit_id.unit_name', string="Unit Name", store=True, tracking=True)
    unit_no = fields.Char(related='unit_id.code', string="Unit Number", store=True, tracking=True)
    owner_code = fields.Char('Code',index=True)

    ###########################################
    # National Address
    ############################################
    pro_block_no = fields.Char(string="Block No", tracking=True)
    pro_street_name = fields.Char(string="Street Name", tracking=True)
    hai_id = fields.Many2one('res.country.state',string="Hay Name", tracking=True)
    pro_city_name = fields.Char(string="City Name", tracking=True)
    mail_code = fields.Char(string="Mail Code", tracking=True)
    extension_num = fields.Char(string="Extension Number", tracking=True)
    national_address = fields.Char(string="National Address",compute="compute_national_address",store=True, tracking=True)
    id_source_location = fields.Many2one('realestate.city',string="Identiti Location", tracking=True)
    fax_code = fields.Char(string="Fax")


    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=None):
        args = args or []
        recs = self.browse()        
        recs = self.search(['|', ('name', operator, name), ('phone', operator, name)] + args,)
        if not recs:
            recs = self.search([('name', operator, name)] + args, )
        return super(res_partner, self).name_search(name, args=args, operator=operator, limit=limit)


    @api.depends('pro_block_no','pro_street_name','hai_id','pro_city_name','mail_code','extension_num')
    def compute_national_address(self):
        for rec in self:
            if rec.pro_block_no and rec.pro_street_name and rec.hai_id.name and rec.pro_city_name and rec.mail_code and rec.extension_num:
                rec.national_address = rec.pro_block_no + '-' + rec.pro_street_name + '-' + rec.hai_id.name + '-' + rec.pro_city_name + '-' + rec.mail_code + '-'  + rec.extension_num

    
    @api.model
    def get_seq_to_view(self):
        sequence = self.env['ir.sequence'].search([('code', '=', self._name)])
        return sequence.sequence.number_next_actual



