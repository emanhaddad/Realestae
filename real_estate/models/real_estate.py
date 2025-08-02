from odoo import models, fields, api ,_
from datetime import datetime, timedelta
from odoo.exceptions import UserError, ValidationError


class real_estate(models.Model):
    _name = "real.estate"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Property Name', required=True, tracking=True)
    #asset_id= fields.Many2one('account.asset.asset','Asset Name')
    code = fields.Char('Code',index=True, tracking=True)
    date = fields.Date('Date', default=datetime.today(), tracking=True)
    property_type_id = fields.Many2one('real.estate.type','Property Type', tracking=True)
    address=fields.Char('Address',index=True, tracking=True)
    city=fields.Char('City',index=True, tracking=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", oldname='currency')
    approximate_value= fields.Float(string="Approximate value", tracking=True)
    num_of_share = fields.Float(string="Planned number of shares", tracking=True)
    property_status = fields.Selection([('exellent', 'Exellent'),('verygood','Very Good'),('good','Good'),('acceptable','Acceptable'),('bad','Bad')], "Status", tracking=True)
    owner_ids=fields.Many2many('res.partner', relation="owners_realstate_rel",
        column1="realstate_id",
        column2="owner_id", string='Owners', tracking=True)
    investors_ids=fields.One2many('realestate.investor.line', 'investors_id', string='Investor', tracking=True)
    commission_ids=fields.One2many('realestate.commission.line', 'commission_id', string='Commissions', tracking=True)
    company_id = fields.Many2one('res.company',readonly=True, string='Company', default=lambda self: self.env.user.company_id)
    user_ids = fields.Many2many(
        string="Users",
        comodel_name="res.users",
        relation="users_realstate_rel",
        column1="realstate_id",
        column2="user_id",
        compute='_get_users',
        store=True
    )
    supervisor_id = fields.Many2one(
        comodel_name="hr.employee",
        string="Supervisor",
        tracking=True
    )
    project_id = fields.Many2one(
        comodel_name="project.project",
        string="Project",
        required=True,
        tracking=True
    )
    property_floors = fields.Integer("Floors Number", tracking=True)
    property_total_area = fields.Float("Total Area", tracking=True)
    property_builtup_area = fields.Float("Built-up Area", tracking=True)
    planned_units_number = fields.Integer("Planned Number of Units", tracking=True)
    property_units_number = fields.Integer(string="Number of Units" , readonly=True,compute="compute_unit_numbers")
    property_share_number = fields.Integer(string="Number of Shares" , readonly=True,compute="compute_share_numbers", tracking=True, store=True)
    remain_share_number = fields.Integer(string="Remain Number of Shares Required" , readonly=True,compute="compute_share_numbers", tracking=True, store=True)
    property_share_amount = fields.Integer(string="Shares Total Value" , readonly=True,compute="compute_share_numbers", tracking=True)
    waqf_instrument = fields.Char("No. of Waqf instrument")
    date_instrument = fields.Date('Instrument Date', tracking=True)
    donor_name=fields.Char('Donor Name',index=True, tracking=True)
    date_donor = fields.Date('Donor Date', tracking=True)
    Property_deed=fields.Char("No. of Property deed", tracking=True)
    date_Property_deed = fields.Date('Property Deed Date', tracking=True)
    state = fields.Selection([('0','Empty')],'State',default="0",index=True,  readonly=True, copy=False)
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority', tracking=True)
    
   
    stores_number=fields.Integer("Number of Stores", tracking=True)
    supplements_number=fields.Integer("Number of Supplements", tracking=True)
    is_guard = fields.Selection([("yes","Yes"),("no","NO")],'Guard', tracking=True)
    google_map_partner = fields.Char(string="Map", tracking=True)
    street = fields.Char(tracking=True)
    street2 = fields.Char(tracking=True)
    zip = fields.Char(change_default=True, tracking=True)
    city = fields.Char(tracking=True)
    state_id = fields.Many2one("res.country.state", string='State', ondelete='restrict', tracking=True)
    country_id = fields.Many2one('res.country', string='Country', ondelete='restrict', tracking=True)
    unit_ids=fields.One2many('real.estate.units', 'base_property_id', string='Unit', tracking=True)
    asanseer_nums = fields.Integer(string='Asanseer Nums', tracking=True)
    pro_block_no = fields.Char(string="Block No", tracking=True)
    pro_street_name = fields.Char(string="Street Name", tracking=True)
    hai_id = fields.Many2one('res.country.state',string="Hay Name", tracking=True)
    pro_city_id = fields.Many2one('realestate.city', string="City Name", tracking=True)
    mail_code = fields.Char(string="Mail Code", tracking=True)
    extension_num = fields.Char(string="Extension Number", tracking=True)
    national_address = fields.Char(string="National Address",compute="compute_national_address",store=True, tracking=True)
    description = fields.Text("Desecription", tracking=True)
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments',store=True, tracking=True)
    # TODO add by belal
    electricity_supply_account_number = fields.Char(string='Electricity supply account number', tracking=True)
    # TODO add by belal
    water_supply_account_number = fields.Char(string='Water supply account number', tracking=True)
    bulding_image_ids = fields.Many2many(
        string="Images",
        comodel_name="ir.attachment",
        relation="real_estate_attachments_rel",
        column1="realestate_id",
        column2="attachment_id",
    )
    property_charact = fields.Selection(
        selection=[('share','Share'),
                    ('under_construc','Under Construction ')], 
        required=True, 
        tracking=True,
        store=True, 
        default='share', 
        string='Property Characteristics')
    date = fields.Date(string='Sale Date', index=True, tracking=True)
    delivery_date = fields.Date(string='Delivery Date', tracking=True)
    remain_days = fields.Float(string="Remain Days to Deliver", compute='compute_remain_days')

    @api.depends('owner_ids')
    def compute_remain_days(self):
        for rec in self:
            if rec.owner_ids:
                owner_dates = rec.owner_ids.mapped('date')
                owner_dates = [date for date in owner_dates if date]
                if owner_dates:
                    first_date = min(owner_dates)
                    today = fields.Date.today()
                    delta = first_date - today
                    rec.remain_days = delta.days
                else:
                    rec.remain_days = 0
            else:
                rec.remain_days = 0


    '''
    @api.onchange('asset_id')
    def no_charss(self):
        self.name = self.asset_id.name
    '''

    @api.depends('company_id')
    def _get_users(self):
        user_ids = [line.id for line in self[0].company_id.supervisor_role_id.users]
        self.user_ids = [(6, 0, user_ids)]

    @api.depends('unit_ids')
    def compute_unit_numbers(self):
        for rec in self:
            if rec.unit_ids :
                rec.property_units_number = len(rec.unit_ids)
            else:
                rec.property_units_number = 0

    @api.depends('investors_ids')
    def compute_share_numbers(self):
        for rec in self:
            if rec.investors_ids :
                rec.property_share_number = sum(line.shares for line in rec.investors_ids)
                rec.property_share_amount = sum(line.commission_amount for line in rec.investors_ids)
                rec.remain_share_number = rec.num_of_share - rec.property_share_number
            else:
                rec.property_share_number = 0
                rec.property_share_amount = 0
                rec.remain_share_number = 0

    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'real.estate'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0) 

   

    def attachment_tree_view(self):
        domain = ['&', ('res_model', '=', 'real.estate'), ('res_id', 'in',self.ids)]
        res_id = self.ids and self.ids[0] or False     
        return {
          'name': _('Attachments'),           
          'domain': domain,          
          'res_model': 'ir.attachment', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form,kanban',
          'help': _('''<p class="oe_view_nocontent_create">
           
                                    Attach
    documents of your employee.</p>'''),
         'limit': 80,
         'context': "{'default_res_model': '%s','default_res_id': %d}"% (self._name, res_id)}

    @api.constrains('pro_block_no','extension_num')
    def address_validation(self):
        if self.pro_block_no :
            if len(self.pro_block_no) > 4 or len(self.pro_block_no) < 4:
                raise ValidationError(_('Block No Must be 4 numbers'))
        if self.extension_num :
            if len(self.extension_num) > 4 or len(self.extension_num) < 4:
                raise ValidationError(_('Extension Number Must be 4 numbers'))

    @api.depends('pro_block_no','pro_street_name','hai_id','pro_city_id','mail_code','extension_num')
    def compute_national_address(self):
        for rec in self:
            if rec.pro_block_no and rec.pro_street_name and rec.hai_id.name and rec.pro_city_id and rec.mail_code and rec.extension_num:
                rec.national_address = rec.pro_block_no + '-' + rec.pro_street_name + '-' + rec.hai_id.name + '-' + rec.pro_city_id.name + '-' + rec.mail_code + '-'  + rec.extension_num

    @api.constrains('income_amount','property_floors')
    def income_amount_validation(self):
        # removed based on requirment, income_amount can hold zero value
        if self.income_amount < 0.0 :
            raise ValidationError(_('Income Amount cannot be zero or less'))
        if self.property_floors < 0.0 :
            raise ValidationError(_('Property Floors cannot be less than zero'))


class real_estate_type(models.Model):
    _name = "real.estate.type"
    _rec_name='name'

    code=fields.Char('Code')
    name=fields.Char('Name')
    type = fields.Selection([('property','property'),('units','Units')],string="Type")
    active = fields.Boolean(
        string='Active', default=True,
        help="If unchecked, it will allow you to hide the product without removing it.")


class res_country_state(models.Model):
    _inherit = "res.country.state"

    country_id = fields.Many2one('res.country', string='Country', required=False)


class RealestateCity(models.Model):
    _name = "realestate.city"
    
    code = fields.Char('City')
    name = fields.Char('Name')

class RealestateCityInvestor(models.Model):
    _name = "realestate.investor.line"
    
    investors_id = fields.Many2one('real.estate')
    name = fields.Many2one('res.partner', string='Name')
    commission_type= fields.Selection([('fixed','Fixed'),('ratio','Ratio')], default='fixed')
    commission_amount= fields.Float(string="Commission amount")
    shares = fields.Integer(string='Number of Shares')
    sign_date = fields.Date('Signing date')
    deliver_date = fields.Date('Deliver date')

class RealestateCityCommission(models.Model):
    _name = "realestate.commission.line"
    
    commission_id = fields.Many2one('real.estate')
    name = fields.Many2one('res.partner', string='Name')
    commission_type= fields.Selection([('fixed','Fixed'),('ratio','Ratio')], default='fixed')
    commission_amount= fields.Float(string="Commission amount")
    date = fields.Date('Date', default=datetime.today())




