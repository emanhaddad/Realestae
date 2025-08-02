
from odoo import api, fields, models


class RealEstate(models.Model):

    _inherit = 'real.estate'

    expenses_ids = fields.One2many(
        'expense.request',
        'property_id',
        'Expenses Logs'
    )

    expenses_count = fields.Integer(
        compute="_compute_expenses_count",
        string='# Expenses Count')

 

    @api.depends('expenses_ids')
    def _compute_expenses_count(self):
        for rec in self:
            rec.expenses_count = len(
                rec.expenses_ids)

    def action_view_expenses(self):
        action = self.env.ref(
            "real_estate_expenses.action_expense_request").read()[0]
        if self.expenses_count > 1:
            action["domain"] = [("id", "in", self.expenses_ids.ids)]
        else:
            action["views"] = [(
                self.env.ref(
                    "real_estate_expenses.expense_request_form").id,
                "form"
            )]
            action["res_id"] = \
                self.expenses_ids and self.expenses_ids.ids[0] or False
        return action


class real_estate_units(models.Model):

    _inherit = 'real.estate.units'

    expenses_ids = fields.One2many(
        'expense.request',
        'unit_id',
        'Expenses Logs',
    )

    expenses_count = fields.Integer(
        compute="_compute_expenses_count",
        string='# Expenses Count')

    @api.depends('expenses_ids')
    def _compute_expenses_count(self):
        for rec in self:
            rec.expenses_count = len(
                rec.expenses_ids)

    def action_view_expenses(self):
        action = self.env.ref(
            "real_estate_expenses.action_expense_request").read()[0]
        if self.expenses_count > 1:
            action["domain"] = [("id", "in", self.expenses_ids.ids)]
        else:
            action["views"] = [(
                self.env.ref(
                    "real_estate_expenses.expense_request_form").id,
                "form"
            )]
            action["res_id"] = \
                self.expenses_ids and self.expenses_ids.ids[0] or False
        return action


