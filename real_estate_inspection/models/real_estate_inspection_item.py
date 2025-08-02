

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class RealEstateInspectionItem(models.Model):

    _name = 'real.estate.inspection.item'
    _description = 'Real Estate Inspection Item'

    name = fields.Char(required=True)
    note = fields.Html('Notes')
    active = fields.Boolean(default=True)

class RealEstateInspectionTemplateLine(models.Model):

    _name = 'real.estate.inspection.template.line'
    _description = 'Real Estate Inspection Item'

    item_id = fields.Many2one('real.estate.inspection.item','Item',required=True)
    template_id = fields.Many2one('real.estate.inspection.template','Item')
    weight=fields.Float(string="Weight")

    @api.constrains('item_id')
    def constrains_item_id(self):
        for line in self:

            item=self.env['real.estate.inspection.template.line'].search([('item_id', '=',line.item_id.id),('template_id', '=',line.template_id.id),('id', '!=',line.id)])
            print("line----------------",line)
            if item:
                raise UserError(_(
                                'An item cannot be configured more than once'
                            ))
   
class RealEstateInspectionTemplate(models.Model):

    _name = 'real.estate.inspection.template'
    _description = 'Real Estate Inspection Template'

    name = fields.Char(required=True)
    note = fields.Html('Notes')
    template_line_ids = fields.One2many('real.estate.inspection.template.line', 'template_id',string='Items')
    active = fields.Boolean(default=True)

    @api.constrains('template_line_ids')
    def onchange_template_line_ids(self):
        if self.template_line_ids:
        	total=sum(self.mapped('template_line_ids.weight'))
        	if total!=100:
        		raise UserError(_(
                            'Total Of Items Weight must be 100%'
                        ))


class appreciationSetting(models.Model):
    _name = "appreciation.setting"

    status = fields.Selection([('exellent', 'Exellent'),('verygood','Very Good'),('good','Good'),('acceptable','Acceptable'),('bad','Bad')], "Appreciation",required=True)
    from_degree = fields.Float(string='from',required=True)
    to_degree = fields.Float(string='to',required=True)

    _sql_constraints = [('uniq_name_status', 'UNIQUE(status)',
                _('The appreciation cannot be configured more than once'))]


    @api.constrains('from_degree')
    def onchange_from_degree(self):
        appreciation=self.env['appreciation.setting'].search([('from_degree', '<=',self.from_degree),('to_degree', '>=',self.from_degree),('id', '!=',self.id)])
        print("appreciation----------------",appreciation)
        if appreciation:
            raise UserError(_(
                            'From Degree Overlaped'
                        ))


    @api.constrains('to_degree')
    def onchange_to_degree(self):
        appreciation=self.env['appreciation.setting'].search([('from_degree', '<=',self.to_degree),('to_degree', '>=',self.to_degree),('id', '!=',self.id)])

        if appreciation:
            raise UserError(_(
                            'To Degree Overlaped'
                        ))
       
       





