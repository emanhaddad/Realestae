# -*- coding: utf-8 -*-
from odoo import api, fields, models, _


class res_company(models.Model):
    _inherit = 'res.company'

    supervisor_role_id = fields.Many2one(
        string="Supervisor group",
        comodel_name="res.groups",
    )
    property_partner_id = fields.Many2one(
        string="Property Partner",
        comodel_name="res.partner",
        domain=[('partner_type', '=', 'supervisor')]
    )


class res_config_settings(models.TransientModel):
    _inherit = 'res.config.settings'

    supervisor_role_id = fields.Many2one(
        string="Supervisor Group",
        comodel_name="res.groups",
        related="company_id.supervisor_role_id",
        readonly=False
    )
    property_partner_id = fields.Many2one(
        string="Property Partner",
        comodel_name="res.partner",
        related="company_id.property_partner_id",
        readonly=False
    )