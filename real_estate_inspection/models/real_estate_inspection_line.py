

from odoo import api, fields, models

class RealEstateInspectionLine(models.Model):

    _name = 'real.estate.inspection.line'
    _description = 'Real Estate Inspection Line'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    READONLY_STATES = {
        'confirmed': [('readonly', True)],
        'cancel': [('readonly', True)],
    }

    inspection_id = fields.Many2one(
        'real.estate.inspection',
        string='Inspection Reference',
        required=True,
        ondelete='cascade',
        index=True,
        copy=False)

    weight=fields.Float(string="Weight")


    inspection_item_id = fields.Many2one(
        'real.estate.inspection.item',
        'Inspection Item',
        required=True,
        track_visibility="onchange",
        help='Inspection Item',
        states=READONLY_STATES,
    )

    result = fields.Selection([
        ('todo', 'Todo'),
        ('success', 'Success'),
        ('failure', 'Failure')
    ], 'Result', default='todo',
        help='Inspection Line Result ',
        readonly=True,
        required=True,
        copy=False
    )

    state = fields.Selection([
        ('draft', 'Draft'),
        ('confirmed', 'Confirmed'),
        ('cancel', 'Cancelled'),
    ], related='inspection_id.state',
        string='Inspection Status',
        readonly=True,
        copy=False,
        store=True,
        default='draft'
    )

    note = fields.Html('Notes')

    status_percentage=fields.Float(string="Status Percentage",required=True,readonly=False,widgets='Percentage',default= 0.00)


    def action_item_result(self):
        if self.status_percentage>=40:
            self.write({'result': 'success'})
        else:
            self.write({'result': 'failure'})
        self.write({'state': 'confirmed'})

    @api.constrains('status_percentage')
    def constrains_status_percentage(self):
        for line in self:

            if line.status_percentage>100:
                raise UserError(_(
                                'Item percentage cannot be grater than 100'
                            ))
   
        
