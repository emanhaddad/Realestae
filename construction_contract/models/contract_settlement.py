#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ProjectContractSettlement(models.Model):
    _name ='project.contract.settlement'
    _description = 'Project Contract Settlement'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date DESC, id DESC'
    _check_company_auto = True

    name = fields.Char(string='Settlement ID', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: 'New')

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('project.settlement',
                                                                     sequence_date=seq_date) or '/'
        res = super(ProjectContractSettlement, self_comp).create(vals)

        return res

    date = fields.Date(string='Date', required=True, default=fields.Date.context_today)
    contract_id = fields.Many2one(string='Contract',
                                  comodel_name='project.contract',
                                  required=True, readonly=True, states={'draft': [('readonly', False)]})
    receipt_id = fields.Many2one(string='Receipt',
                                 comodel_name='project.contract.receipt',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]})
    project_id = fields.Many2one(string='Project',
                                 comodel_name='project.project',
                                 related='contract_id.project_id',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]})
    task_id = fields.Many2one(string='Task',
                              comodel_name='project.task',
                              required=True, readonly=True, states={'draft': [('readonly', False)]})
    stage_id = fields.Many2one(string='Stage',
                                 comodel_name='project.task.type',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]})
    company_id = fields.Many2one(string='Company',
                                 comodel_name='res.company',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.company)

    cancel_reason_id = fields.Many2one(string='Cancellation Reason',
                                       comodel_name='project.construction.cancel.reason',
                                       readonly=True, copy=False)
    cancel_reason = fields.Text(string='Cancellation Notes',
                                readonly=True,
                                # The wizard will write the reason notes here.
                                # states={'cancel': [('readonly', False)],
                                #         'reject': [('readonly', False)]},
                                copy=False)
    cancel_date = fields.Datetime(string='Cancellation Date', readonly=True, copy=False)

    state = fields.Selection(string='Status',
                             selection=[('draft', 'Draft'),
                                        ('open', 'Open'),
                                        ('done', 'Done'),
                                        ('cancel', 'Cancelled')],
                             required=True, readonly=True, copy=False, tracking=True, default='draft')

    def set_confirm(self):
        for settlement in self:
            if settlement.state == 'draft':
                settlement.state = 'open'
            else:
                raise UserError(_('You can only confirm draft settlements.'))

    def set_done(self):
        for settlement in self:
            if settlement.state == 'open':
                settlement.state = 'done'
            else:
                raise UserError(_('You can only done open settlements.'))

    def set_cancel(self):
        self.ensure_one()
        if self.state not in ['draft', 'open']:
            raise UserError(_('You cannot cancel a settlement which draft and open states.'))
        return {
            'name': _('Cancel Settlement'),
            'view_mode': 'form',
            'res_model': 'construction.reject.wizard',
            'view_id': self.env.ref('construction_contract.construction_contract_reject_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_settlement_id': self.id, 'reject': False, 'field': 'settlement_id'},
            'target': 'new'
        }

    def unlink(self):
        for settlement in self:
            if not settlement.state == 'draft':
                raise UserError(_('You can only delete draft settlements. Cancel it instead.'))
        return super(ProjectContractSettlement, self).unlink()
