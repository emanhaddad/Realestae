from odoo import models, fields, api
from odoo.exceptions import ValidationError, AccessError,UserError


class property_evaluation(models.Model):
    _name = "property.evaluation"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name='property_id'

    property_id = fields.Many2one('real.estate', string="Property", tracking=True)
    supervisor_id = fields.Many2one(related="property_id.supervisor_id", string="Supervisor", tracking=True)
    state_id = fields.Many2one(comodel_name="res.country.state", related="property_id.hai_id", string="Neighborhood", tracking=True)
    area = fields.Float(related="property_id.property_total_area", string="Total Area", tracking=True)
    property_type_id = fields.Many2one(related="property_id.property_type_id", string="Property Type", tracking=True)
    date = fields.Date(related="property_id.date", string="Creation date", tracking=True)
    # TODO modifide by belal ( Integer => Float , property_floor => property_builtup_area)
    surfaces = fields.Float(related="property_id.property_builtup_area", string="Total Property surfaces",default=0, tracking=True)
    unit_no = fields.Integer(tracking=True, related="property_id.property_units_number", string="Number of Units")
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", oldname='currency')
    real_estate_office= fields.Float(string="Real Estate Office Estimation",required=True)
    annual_income= fields.Float( string="Annual Income",required=True)
    estimated_meter_value= fields.Float(string="Estimated ground meter cost",required=True)
    estimated_meter_construction= fields.Float(string="Estimated construction meter cost",required=True)
    meter_area= fields.Float(string="Area*Meter",required=True, compute="compute_all",store=True, tracking=True)
    total_construction_costs= fields.Float(string="Total construction costs", compute="compute_all",store=True, tracking=True)
    property_estimated_cost= fields.Float(string="Property Estimated Cost", compute="compute_all",store=True, tracking=True)
    # TODO  add by belal - calculates the avrage cost of the property using 2 other fields
    property_avrage_cost = fields.Float(string="The Average Cost", compute="compute_all",store=True,default=0.00)
    investment_income= fields.Float(string="Percentage of the income of the property of the Investment Department", compute="compute_all",store=True,)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('review', 'Reviewed'),
                              ('premeditated', 'premeditated'),
                              ('premeditation', 'Financial management premeditation')],
                             'State', readonly=True,default='draft', tracking=True)
    land_prise = fields.Float(compute="compute_all",string="Total Land Prise",store=True, tracking=True)

    def unlink(self):
        for record in self:
            if record.state not in ('draft'):
                raise UserError(_('Sorry! You cannot delete evaluation record not in Draft state.'))
        return models.Model.unlink(self)

    @api.onchange('annual_income')
    def _onchange_annual_income(self):
        self.ensure_one()
        if self.property_id:
            return {
                'annual_income':self.property_id.income_amount or 0.0
            }

    @api.depends('area','estimated_meter_value','total_construction_costs','annual_income','surfaces','estimated_meter_value','real_estate_office')    
    def compute_all(self):
        meter_area = self.estimated_meter_value * self.area
        total_construction_costs  = self.surfaces * self.estimated_meter_construction
        land_prise = self.area * self.estimated_meter_value
        property_estimated_cost = land_prise + total_construction_costs
        real_estate_office = self.real_estate_office
        # TODO  add by belal 
        property_avrage_cost = (property_estimated_cost + real_estate_office) / 2
        if self.annual_income > 0 and property_estimated_cost > 0 :
            investment_income = (self.annual_income /property_estimated_cost) *100
        else : 
            investment_income = 0 
        self.meter_area = meter_area
        self.total_construction_costs = total_construction_costs
        self.land_prise = land_prise
        self.property_estimated_cost = property_estimated_cost
        self.investment_income = investment_income
        # TODO  add by belal 
        self.property_avrage_cost = property_avrage_cost
        return True

    def confirm(self):
        return self.write({'state': 'confirm'})

    def review(self):
        return self.write({'state': 'review'})

    def premeditated(self):
        return self.write({'state': 'premeditated'})

    def premeditation(self):
        return self.write({'state': 'premeditation'})