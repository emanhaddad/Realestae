
from odoo import api, fields, models
from dateutil.relativedelta import relativedelta


class RealEstate(models.Model):

    _inherit = 'real.estate'

    maintenance_ids = fields.One2many(
        'real.estate.maintenance',
        'real_estate_id',
        'Maintenance Logs'
    )

    maintenance_count = fields.Integer(
        compute="_compute_maintenance_count",
        string='# Maintenance Count')
    commission_type= fields.Selection([('fixed','Fixed'),('ratio','Ratio')], default='fixed')
    commission_amount= fields.Monetary(string="Commission amount")
    warranty_start_date = fields.Date('Warranty start date')
    warranty_end_date = fields.Date('Warranty end date')
    unit_profit_ids=fields.One2many('profits.count.line', inverse_name='profit_id', string='Unit Profit', tracking=True)
    property_line_ids=fields.One2many('property.profits.count', inverse_name='profit_id', string='Property Profit', tracking=True)

    # @api.onchange('warranty_start_date')
    # def onchange_warranty_beggining(self):
    #     if self.warranty_start_date:
    #         self.warranty_end_date = self.warranty_start_date+ relativedelta(years=1)
    
    @api.depends('maintenance_ids')
    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = len(
                rec.maintenance_ids)

    def action_view_maintenance(self):

        views = [(self.env.ref('real_estate_maintenance.maintenance_request_view_tree').id, 'tree'), (self.env.ref('real_estate_maintenance.real_estate_maintenance_view_form').id, 'form')]
        return{
            'name': 'Maintenance Request',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'real.estate.maintenance',
            'views': views,
            'domain':[("id", "in", self.maintenance_ids.ids)],
            'type': 'ir.actions.act_window',
        }          
        


class real_estate_units(models.Model):

    _inherit = 'real.estate.units'

    maintenance_ids = fields.One2many(
        'real.estate.maintenance',
        'unit_id',
        'Maintenance Logs'
    )

    maintenance_count = fields.Integer(
        compute="_compute_maintenance_count",
        string='# Maintenance Count')
    
    

    @api.depends('maintenance_ids')
    def _compute_maintenance_count(self):
        for rec in self:
            rec.maintenance_count = len(
                rec.maintenance_ids)

    def action_view_maintenance(self):
        views = [(self.env.ref('real_estate_maintenance.maintenance_request_view_tree').id, 'tree'), (self.env.ref('real_estate_maintenance.maintenance_request_view_form').id, 'form')]
        return{
            'name': 'Maintenance Request',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'view_id': False,
            'res_model': 'real.estate.maintenance',
            'views': views,
            'domain':[("id", "in", self.maintenance_ids.ids)],
            'type': 'ir.actions.act_window',
        }     

