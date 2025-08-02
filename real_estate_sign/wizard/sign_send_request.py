# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
from odoo import fields, models


class SignSendRequest(models.TransientModel):
    _inherit = "sign.send.request"

    contract_id = fields.Many2one("realestate.contract.model", string="Contract")

    def create_request(self, send=True, without_mail=False):
        request_info = super(SignSendRequest, self).create_request(send, without_mail)
        request_id = request_info["id"]
        if self.contract_id:
            request = self.env["sign.request"].browse(request_id)
            request.contract_id = self.contract_id
        return request_info
