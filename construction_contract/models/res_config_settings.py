#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    # Construction Contract
    ceo_user_id = fields.Many2one(readonly=False,
                                  related='company_id.ceo_user_id')
    construction_receipt_body = fields.Html(related='company_id.construction_receipt_body',
                                            readonly=False)


class ResCompany(models.Model):
    _inherit = 'res.company'

    # Construction Contract
    ceo_user_id = fields.Many2one(string='CEO User',
                                  comodel_name='res.users',
                                  required=False,
                                  default=lambda self: self.env.ref('base.user_root', raise_if_not_found=False))
    construction_receipt_body = fields.Html(string='Construction Receipt Body', translate=True)
