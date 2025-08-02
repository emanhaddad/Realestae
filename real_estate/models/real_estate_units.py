from odoo import models, fields, api
from odoo.exceptions import UserError, ValidationError
from odoo import models, fields, api ,_
from datetime import datetime, timedelta


class real_estate_units(models.Model):
    _name = "real.estate.units"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name='unit_name'

    @api.depends('code','base_property_id')
    def compute_unit_name(self):
        for rec in self:
            if rec.code and rec.base_property_id.name:
                rec.unit_name = f"{rec.base_property_id.name} - {rec.code}"
            else:
                rec.unit_name = rec.code

    code = fields.Char(string='Code',index=True)
    unit_name=fields.Char(index=True, compute='compute_unit_name', tracking=True)
    date = fields.Date('Date',default=fields.Date.today, tracking=True)
    property_type_id = fields.Many2one('real.estate.type','Unit Type', tracking=True)
    base_property_id = fields.Many2one('real.estate','Base Property', tracking=True)
    unit_space=fields.Float(string='Space', tracking=True)
    currency_id = fields.Many2one('res.currency', tracking=True, help='The currency used to enter statement', string="Currency", oldname='currency')
    unit_amount= fields.Monetary(string="Unit Net Price", tracking=True, compute='compute_unit_price', store=True)
    unit_price= fields.Monetary(string="Unit Price", tracking=True)
    unit_taxes= fields.Monetary(string="Unit taxes", tracking=True)
    commission_type= fields.Selection([('fixed','Fixed'),('ratio','Ratio')], default='fixed', tracking=True)
    unit_commission= fields.Monetary(string="Unit commission", tracking=True)
    electricity_bill_amount= fields.Monetary(string="Electricity Bill Amount by month", tracking=True)
    water_bill_amount= fields.Monetary(string="Water Bill Amount by year", tracking=True)
    property_floors = fields.Many2one('floors.model' ,string="Floor Number", tracking=True)
    property_rooms = fields.Integer("Rooms Number", tracking=True)
    property_type = fields.Selection([('ready','Ready'),('under_construction','Under construction'),('final_prepare','Final prepare')], required=True, default='under_construction', tracking=True)
    description=fields.Text('Description',index=True, tracking=True)
    maintenanace_account_value = fields.Monetary("Maintenanace Account Value", tracking=True)
    
    prople_no = fields.Integer("Maximum People Number", tracking=True)
    content_rel=fields.One2many('content.line', 'relation', string='Content', tracking=True)
    cost_duration = fields.Selection([('yearly','Yearly'),('monthly','Monthly')],string="Cost Duration",default='yearly', tracking=True)
    #asset_tied = fields.Boolean(string="Tied with assets")
    copmute_code =  fields.Boolean(string='Copmute Code',help='this field is just used to call function that update the code ',compute="compute_code")
    # TODO add by belal
    electricity_supply_account_number = fields.Char(string='Electricity supply account number', tracking=True)
    water_supply_account_number = fields.Char(string='Water supply account number', tracking=True)
    unit_status = fields.Selection([('exellent', 'Exellent'),('verygood','Very Good'),('good','Good'),('acceptable','Acceptable'),('bad','Bad')], "Status", tracking=True)
    state = fields.Selection([('available', 'Available'),('booked', 'Booked'),('sold','Sold'),('evacuate','Evacuate'),('rent','Rent'),('delivered','Delivered'),('delegated', 'Delegated'),('re_sold','Resold')], "State", default="available",copy=False, tracking=True)
    unit_image_ids = fields.Many2many(
        string="Images",
        comodel_name="ir.attachment",
        relation="real_estate_unit_attachments_rel",
        column1="realestate_id",
        column2="attachment_id",
        tracking=True
    )
    buyer_id = fields.Many2one('res.partner', 'Buyer', tracking=True)
    owner_id = fields.Many2one('res.partner', 'Owner', tracking=True)
    renter_id = fields.Many2one('res.partner', 'Renter', tracking=True)
    evaluation_ids = fields.One2many('unit.evaluation.line', 'evaluation_id', tracking=True)
    priority = fields.Selection([('0', 'Very Low'), ('1', 'Low'), ('2', 'Normal'), ('3', 'High')], string='Priority', tracking=True)
    construc_date = fields.Date('Date of Construction Complete', tracking=True)
    unit_age = fields.Float('Unit age', readonly=True, compute="compute_unit_age", tracking=True)
    profit_calculated = fields.Boolean('Profit Calculated', default=False, tracking=True, readonly=True)

    @api.depends('unit_price', 'unit_taxes', 'unit_commission')
    def compute_unit_price(self):
        for rec in self:
            rec.unit_amount = rec.unit_price + rec.unit_taxes + rec.unit_commission

    @api.model
    def create(self, vals):
        base_property = self.env['real.estate'].browse(vals.get('base_property_id'))
        if base_property:
            planned_units_number = base_property.planned_units_number
            property_units_number = base_property.property_units_number

            if property_units_number >= planned_units_number:
                raise UserError(
                    _('You cannot create more units. The number of units (%s) exceeds the planned number (%s).') % 
                    (property_units_number, planned_units_number)
                )

        return super(real_estate_units, self).create(vals)

    @api.depends('construc_date')
    def compute_unit_age(self):
        today = fields.date.today()
        for record in self:
            if record.construc_date:
                delta = today - record.construc_date
                record.unit_age = delta.days / 365.25
            else:
                record.unit_age = 0


    @api.onchange('base_property_id')
    def compute_water_elctroicity_account(self):
        if self.base_property_id.water_supply_account_number:
            self.water_supply_account_number = self.base_property_id.water_supply_account_number
        if self.base_property_id.electricity_supply_account_number:
            self.electricity_supply_account_number = self.base_property_id.electricity_supply_account_number

    

    @api.depends('electricity_account_value','water_account_value')
    def bill_calaulation(self):
        self.electricity_bill_amount = self.electricity_account_value + self.water_account_value


    @api.constrains('code')
    def _check_code_uniqueness(self):
        units = self.env['real.estate.units'].search([('id','!=',self.id),('code','=',self.code),('base_property_id','=',self.base_property_id.id)])
        if units:
            raise ValidationError(_('There Is other Units In This Property Have The Same Code'))




class ContentLine(models.Model):
    _name = "content.line"

    content = fields.Many2one('content.setting',string='Content')
    code = fields.Char('Code')
    quantity = fields.Integer("Quantity")
    relation = fields.Many2one('real.estate.units',string='relation')
    content_name = fields.Char(related="content.name", string='Name', store=True)
    content_code = fields.Char(related="content.code", string='Code', store=True)
    note = fields.Char(string="Note")



class floors_model(models.Model):
    _name = "floors.model"

    name = fields.Char(string='Floor Name', tracking=True)



class ContentSetting(models.Model):
    _name = "content.setting"
    
    name = fields.Char(string="Name", tracking=True)
    code = fields.Char('Code', tracking=True)


class UnitEvaluation(models.Model):
    _name = "unit.evaluation.line"
    
    evaluation_id = fields.Many2one('real.estate.units', tracking=True)
    amount = fields.Float(string="Evaluation Amount", tracking=True)
    note = fields.Char('Notes/ Comments', tracking=True)
