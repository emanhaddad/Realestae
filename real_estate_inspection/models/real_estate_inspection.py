

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RealEstateInspection(models.Model):

    _name = 'real.estate.inspection'
    _description = 'real Estate Inspection'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    READONLY_STATES = {
        'confirmed': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    name = fields.Char(
        'Reference',
        required=True,
        index=True,
        copy=False,
        default='New'
    )

    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        required=True,
        states=READONLY_STATES
    )

    inspection_type = fields.Selection([('all_property','All property'),('specific_units','Specific Units')],readonly=True,string="Inspection Type")
    unit_id = fields.Many2one('real.estate.units', string="Unit")
    renter_id=fields.Many2one("res.partner", "Renter" , ondelete="cascade",store=True)
    old_property_status = fields.Selection([('exellent', 'Exellent'),('verygood','Very Good'),('good','Good'),('acceptable','Acceptable'),('bad','Bad')], "Old Property Status")
    new_property_status = fields.Selection([('exellent', 'Exellent'),('verygood','Very Good'),('good','Good'),('acceptable','Acceptable'),('bad','Bad')], "New Property Status")
    old_unit_status = fields.Selection([('exellent', 'Exellent'),('verygood','Very Good'),('good','Good'),('acceptable','Acceptable'),('bad','Bad')], "Old Unit Status")
    new_unit_status = fields.Selection([('exellent', 'Exellent'),('verygood','Very Good'),('good','Good'),('acceptable','Acceptable'),('bad','Bad')], "New Unit Status")

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], string='Status',
        copy=False, index=True, readonly=True, track_visibility='onchange',
        default='draft',
        help=" * Draft: not confirmed yet.\n"
             " * Confirmed: inspection has been confirmed.\n"
             " * Cancelled: has been cancelled, can't be confirmed anymore.")

    contract_id = fields.Many2one('realestate.contract.model', string="Rent Contract")
    template_id = fields.Many2one(
        'real.estate.inspection.template',
        'Inspection Template',
        help='Inspection Template',
        required=False,
        states=READONLY_STATES
    )
    date_inspected = fields.Datetime(
        'Inspection Date',
        required=True,
        default=fields.Datetime.now,
        help='Date when the Real State has been inspected',
        copy=False,
        states=READONLY_STATES,
    )
    inspected_by = fields.Many2one(
        'res.partner',
        'Inspected By',
        track_visibility="onchange",
        help='Inspected By',
        states=READONLY_STATES,
    )
    note = fields.Html('Notes', states=READONLY_STATES)
    inspection_line_ids = fields.One2many(
        'real.estate.inspection.line',
        'inspection_id',
        string='Inspection Lines',
        copy=True,
        auto_join=True,
        states=READONLY_STATES,
    )
    unit_inspection_ids = fields.One2many(
        'real.estate.inspection',
        'real_state_inspection_id',
        string='Units Inspection',
    )
    real_state_inspection_id = fields.Many2one(
        'real.estate.inspection',
    )
    status_percentage=fields.Float(string="Status Percentage",required=False,widgets='Percentage',default= 0.00)
    # domain="[('contract_partner_type', '=', rent),('state', '=', confirmed)]"


    @api.onchange('renter_id')
    def _onchange_renter_id(self):
        """Update the domain of contract_id based on the selected renter_id.

        """
        if self.real_estate_id:
            domain = [('partner_id', '=', self.renter_id.id)]
            domain += [('contract_partner_type', '=', 'rent')]
            domain += [('state', '=', 'confirmed')]
        else:
            domain = []
        
        return {'domain': {'contract_id': domain}}


    def get_inspection_line(self):
        self.inspection_line_ids.unlink()
        if self.template_id and self.template_id.template_line_ids:
            for item in self.template_id.template_line_ids:
                self.env['real.estate.inspection.line'].create({
                            'inspection_id': self.id,
                            'inspection_item_id': item.item_id.id,
                            'weight':item.weight,

                        })

    def get_unit_inspection(self):
        self.unit_inspection_ids.unlink()
        if self.real_estate_id and self.real_estate_id.unit_ids:
            for unit in self.real_estate_id.unit_ids:
                self.env['real.estate.inspection'].create({
                            'real_state_inspection_id':self.id,
                            'real_estate_id':self.real_estate_id.id,
                            'inspection_type':'specific_units',
                            'unit_id':unit.id,
                            'template_id':self.template_id.id,
                            'old_unit_status':unit.unit_status
                        })

    # @api.onchange('real_estate_id','unit_id')
    # def onchange_real_estate_id(self):
    #     for rec in self:         
    #         if rec.inspection_type=='specific_units':
    #             rec.old_unit_status=rec.unit_id.unit_status
    #             if rec.unit_id.renter_id:
    #                 rec.renter_id=rec.unit_id.renter_id
    #             if rec.unit_id.contract_id:
    #                 rec.contract_id=rec.unit_id.contract_id
    #         if rec.inspection_type=='all_property':
    #             rec.old_property_status=rec.real_estate_id.property_status
    #             if rec.real_estate_id.renter_id:
    #                 rec.renter_id=rec.real_estate_id.renter_id
    #             if rec.real_estate_id.contract_id:
    #                 rec.contract_id=rec.real_estate_id.contract_id


    @api.model
    def create(self, vals):
        if vals.get('name', 'New') == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code(
                    'real.estate.inspection') or '/'
        return super(RealEstateInspection, self).create(vals)

    
    def button_cancel(self):
        for inspection in self:
            if inspection.state not in ['draft', 'confirmed']:
                continue
            inspection.write({'state': 'cancel'})
        return True

    
    def button_confirm(self):
        for inspection in self:
            if inspection.inspection_type=='specific_units':
                if inspection.inspection_line_ids:
                    if inspection.state not in ['draft', 'cancel']:
                        continue
                    if (inspection.inspection_line_ids.filtered(
                            lambda x: x.result == 'todo')):
                        raise UserError(_(
                            'Inspection cannot be completed. There are uninspected items.'
                        ))
                    total=0.0
                    for line in inspection.inspection_line_ids:
                        weight=(line.weight)*line.status_percentage/100
                        total+=weight
                    self.status_percentage=total

                    evaluation=self.env['appreciation.setting'].search([('from_degree', '<=', inspection.status_percentage),('to_degree', '>=', inspection.status_percentage) ],limit=1)
                    if evaluation:
                        inspection.write({'new_unit_status':evaluation.status})
                        inspection.unit_id.write({'unit_status':evaluation.status})


                else:
                    raise UserError(_(
                        'Inspection cannot be completed. There are no inspected items.'
                    ))
            else:
                if inspection.unit_inspection_ids:
                    if inspection.state not in ['draft', 'cancel']:
                        continue
                    if (inspection.unit_inspection_ids.filtered(
                            lambda x: x.state == 'draft')):
                        raise UserError(_(
                            'Inspection cannot be completed. There are uninspected Unit.'
                        ))
                else:
                    raise UserError(_(
                        'Inspection cannot be completed. There are no inspected units.'
                    ))

            status_percentage=0.0
            for unit in inspection.unit_inspection_ids:
                status_percentage+=unit.status_percentage
                inspection.status_percentage=status_percentage/len(inspection.unit_inspection_ids)
                evaluation=self.env['appreciation.setting'].search([('from_degree', '<=', inspection.status_percentage),('to_degree', '>=', inspection.status_percentage) ],limit=1)
                if evaluation:
                    inspection.write({'new_property_status':evaluation.status})
                    inspection.real_estate_id.write({'property_status':evaluation.status})




            inspection.write({'state': 'confirmed'})
        return True

    def button_draft(self):
        for inspection in self:
            if inspection.inspection_type=='specific_units':

                inspection.write({'state': 'draft'})
                inspection.inspection_line_ids.write({'result': 'todo'})
            else:
                inspection.unit_inspection_ids.button_draft()
                inspection.write({'state': 'draft'})

        return True

    