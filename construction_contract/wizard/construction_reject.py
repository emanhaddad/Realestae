#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError


class ProjectConstructionReject(models.TransientModel):
    _name = 'construction.reject.wizard'
    _description = 'Construction Construction Reject Wizard'

    contract_id = fields.Many2one(string='Contract',
                                  comodel_name='project.contract')
    receipt_id = fields.Many2one(string='Receipt',
                                 comodel_name='project.contract.receipt')
    settlement_id = fields.Many2one(string='Settlement',
                                    comodel_name='project.contract.settlement')
    reason_id = fields.Many2one(string='Reason',
                                comodel_name='project.construction.cancel.reason',
                                required=True)
    cancel_reason = fields.Text(string='Reason Comment', required=True)

    @api.onchange('reason_id')
    def _onchange_reason_id(self):
        if not self.reason_id:
            return

        self.cancel_reason = self.reason_id.description if self.reason_id.description else self.reason_id.name

    def action_reject(self):
        self.ensure_one()

        if not self.reason_id:
            raise UserError(_('You must select a reason to reject or cancel a contract.'))

        # get the active model and record
        # TODO: @MRawi: Check this and remove relational fields if no use-case can utilize them.
        active_model = self.env.context.get('active_model')
        record = self.env[active_model].browse(self.env.context.get('active_id'))
        if record:
            record.write({
                'state': 'reject' if self.env.context.get('reject') is True else 'cancel',
                'cancel_reason_id': self.reason_id.id,
                'cancel_reason': self.cancel_reason,
                'cancel_date': fields.Datetime.now(),
            })
        else:
            raise ValidationError(_('There is no record to reject or cancel.'))
        return True