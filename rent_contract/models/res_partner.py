from odoo import models, fields, api,_
from odoo.exceptions import ValidationError,UserError
import re


class res_partner(models.Model):
    _inherit = 'res.partner'

    religion = fields.Selection([('muslim','Muslim'),('not_muslim','Not Muslim')],string='Religion',index=True)
    date_release = fields.Date('Identity Issue Date')
    date_end = fields.Date('Issue Finish Date')
    partner_sate = fields.Selection([('single', 'Single'),('married','Married')], "Marital Status")
    chlidren_no = fields.Selection([('0','0'),('1','1'),('2','2'),('3','3'),('4','4'),('5','5'),('6','6'),
        ('7','7'),('8','8'),('9','9'),('10','10'),('11','11'),('12','12'),('13','13'),
        ('14','14'),('15','15'),('16','16'),('17','17'),('18','18'),('19','19'),('20','20'),('more_than','More Than 20')])
    more_children_no = fields.Integer("children number")
    passport_no = fields.Char("Passport Number")
    identiti_no = fields.Char("Identification No")
    account_code = fields.Char('Account Code',index=True)
    contacts= fields.One2many('reference.contacts', 'res_relation', string='References')
    mailbox = fields.Char('P.O. box',index=True)
    address_new = fields.Char(string='Work Address')
    work_location = fields.Char('Work Location')
    work_phone = fields.Char('Work Phone')
    mobile_phone = fields.Char('Work Mobile')
    work_email = fields.Char('Work Email')
    black_list=fields.Boolean(string='Add to Black List')
    reason=fields.Text('Reason',index=True)
    a = fields.Integer("Pr" , default=0)
    country_nath = fields.Many2one('res.country', string='Nationality', ondelete='restrict')
    identity_type = fields.Many2one('identity.types',string='Identity Type')
    renter_code = fields.Char(string="Renter Code")
    # date = fields.Date(string='Sale Date', index=True,)
    # delivery_date = fields.Date(string='Delivery Date')

    @api.model
    def name_search(self, name, args=None, operator='ilike', limit=None):
        args = args or []
        recs = self.browse()        
        recs = self.search(['|', ('name', operator, name), ('mobile_phone', operator, name)] + args,)
        if not recs:
            recs = self.search([('name', operator, name)] + args, )
        return super(res_partner, self).name_search(name, args=args, operator=operator, limit=limit)

    @api.constrains('identiti_no','identity_type')
    def identiti_no_validation(self):
        if self.identiti_no and (self.identity_type.name == identity_types_model.CITIZEN or self.identity_type.name == identity_types_model.RESIDENT) :
            if len(self.identiti_no) > 10 or len(self.identiti_no) < 10:
                raise ValidationError(_('Identiti No Must be 10 numbers'))

    @api.depends('pro_block_no','pro_street_name','hai_id','pro_city_name','mail_code','extension_num')
    def compute_national_address(self):
        for rec in self:
            if rec.pro_block_no and rec.pro_street_name and rec.hai_id.name and rec.pro_city_name and rec.mail_code and rec.extension_num:
                rec.national_address = rec.pro_block_no + '-' + rec.pro_street_name + '-' + rec.hai_id.name + '-' + rec.pro_city_name + '-' + rec.mail_code + '-'  + rec.extension_num

    @api.onchange('reason')
    def add_black_list(self):
        if self.black_list and self.reason:
           if self.black_list== True:
              black_list_data={
                        "name":self.name, 
                        "reason":self.reason,
                        }
              self.env["black.list"].create(black_list_data)

    @api.constrains('work_phone' , 'mobile_phone')
    def check_phone(self):
        pattern = re.compile(r'^\d{9,9}$')
        if self.work_phone:
            if not pattern.search(self.work_phone):
                raise ValidationError(_('work Phone must be exactly 9 Numbers without ZERO 0 .'))
        if self.mobile_phone:
            if not pattern.search(self.mobile_phone):
                raise ValidationError(_('mobile Phone must be exactly 9 Numbers without ZERO 0 .'))

    @api.model
    def get_seq_to_view(self):
        sequence = self.env['ir.sequence'].search([('code', '=', self._name)])
        return sequence.sequence.number_next_actual

    @api.model
    def create(self, vals):
        vals['renter_code'] = self.sudo().env['ir.sequence'].sudo().next_by_code('res.partner.sequence') or '/'
        return super(res_partner, self).create(vals)


class contacts(models.Model):
    _name = "reference.contacts"

    name=fields.Char('Name',index=True)
    address=fields.Char('Address',index=True)
    telephone=fields.Char('Telephone',index=True)
    res_relation = fields.Many2one('res.partner','relation',invisible=1)


class black_list(models.Model):
    _name = "black.list"

    name = fields.Char(string="Name")
    reason=fields.Text('Reason',index=True)


class identity_types_model(models.Model):
    _name = "identity.types"
    
    name = fields.Char(string="Type Name")

    #EXCEPTED VALUES FOR IDENTITY TYPES
    CITIZEN = "مواطن"
    RESIDENT = "مقيم"
