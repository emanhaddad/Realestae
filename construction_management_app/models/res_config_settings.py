#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    module_construction_contract = fields.Boolean(string='Construction Contracts', default=False,
                                                  help='Manage Construction Contracts')
