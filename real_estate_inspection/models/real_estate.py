
from odoo import api, fields, models


class RealEstate(models.Model):

    _inherit = 'real.estate'

    inspection_ids = fields.One2many(
        'real.estate.inspection',
        'real_estate_id',
        domain = [("inspection_type", "=", 'all_property')],
        string='Inspection Logs'
    )

    inspection_count = fields.Integer(
        compute="_compute_inspection_count",
        string='# Inspection Count')

    @api.depends('inspection_ids')
    def _compute_inspection_count(self):
        for rec in self:
            rec.inspection_count = len(
                rec.inspection_ids)

    def action_view_inspection(self):
        action = self.env.ref(
            "real_estate_inspection.real_estate_inspection_act_window").read()[0]
        if self.inspection_count > 1:
            action["domain"] = [("id", "in", self.inspection_ids.ids),("inspection_type", "=", 'all_property')]
        else:
            action["views"] = [(
                self.env.ref(
                    "real_estate_inspection.real_estate_inspection_form_view").id,
                "form"
            )]
            action["res_id"] = \
                self.inspection_ids and self.inspection_ids.ids[0] or False
        return action


class real_estate_units(models.Model):

    _inherit = 'real.estate.units'

    inspection_ids = fields.One2many(
        'real.estate.inspection',
        'unit_id',
        'Inspection Logs'
    )

    inspection_count = fields.Integer(
        compute="_compute_inspection_count",
        string='# Inspection Count')

    @api.depends('inspection_ids')
    def _compute_inspection_count(self):
        for rec in self:
            rec.inspection_count = len(
                rec.inspection_ids)

    def action_view_inspection(self):
        action = self.env.ref(
            "real_estate_inspection.real_estate_inspection_act_window").read()[0]
        if self.inspection_count > 1:
            if self.ontract_type=="specific_units":
                action["domain"] = [("id", "in", self.inspection_ids.ids),("inspection_type", "=", 'specific_units')]
            if self.ontract_type=="all_property":
                action["domain"] = [("id", "in", self.inspection_ids.ids),("inspection_type", "=", 'all_property')]

        else:
            action["views"] = [(
                self.env.ref(
                    "real_estate_inspection.real_estate_inspection_form_view").id,
                "form"
            )]
            action["res_id"] = \
                self.inspection_ids and self.inspection_ids.ids[0] or False
        return action


class RealEstateContract(models.Model):

    _inherit = 'realestate.contract.model'

    inspection_ids = fields.One2many(
        'real.estate.inspection',
        'real_estate_id',
        'Inspection Logs'
    )

    inspection_count = fields.Integer(
        compute="_compute_inspection_count",
        string='# Inspection Count')

    @api.depends('inspection_ids')
    def _compute_inspection_count(self):
        for rec in self:
            rec.inspection_count = len(
                rec.inspection_ids)

    def action_view_inspection(self):
        action = self.env.ref(
            "real_estate_inspection.real_estate_inspection_act_window").read()[0]
        if self.inspection_count > 1:
            action["domain"] = [("id", "in", self.inspection_ids.ids),("inspection_type", "=", 'specific_units')]
        else:
            action["views"] = [(
                self.env.ref(
                    "real_estate_inspection.real_estate_inspection_form_view").id,
                "form"
            )]
            action["res_id"] = \
                self.inspection_ids and self.inspection_ids.ids[0] or False
        return action

