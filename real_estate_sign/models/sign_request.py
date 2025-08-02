# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import api, fields, models, _


class SignRequest(models.Model):
    _inherit = "sign.request"

    contract_id = fields.Many2one("realestate.contract.model", string="Real estate contract")

    def action_signed(self):
        super(SignRequest, self).action_signed()
        for request in self:
            if request.contract_id:
                request.contract_id.message_post_with_view(
                    "real_estate_sign.message_signature_link",
                    values={"request": request, "salesman": self.env.user.partner_id},
                    subtype_id=self.env.ref("mail.mt_note").id,
                    author_id=self.env.user.partner_id.id,
                )
                # attach a copy of the signed document to the SO for easy retrieval
                self.env["ir.attachment"].create(
                    {
                        "name": request.reference,
                        "datas": request.completed_document,
                        "type": "binary",
                        "res_model": self.env["realestate.contract.model"]._name,
                        "res_id": request.contract_id.id,
                    }
                )
