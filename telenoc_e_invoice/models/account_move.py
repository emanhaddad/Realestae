# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api , _


class AccountMove(models.Model):
    _inherit = 'account.move'

    narration = fields.Text(translate=True)
    n_name = fields.Char(string="New name", compute="_compute_new_name" )

    def _get_name_invoice_report(self):
        self.ensure_one()
        if self.company_id.country_id.code == 'SA':
            return 'telenoc_e_invoice.arabic_english_invoice'
        return super()._get_name_invoice_report()

    def _get_move_display_name(self, show_ref=False):
        ''' Helper to get the display name of an invoice depending of its type.
        :param show_ref:    A flag indicating of the display name must include or not the journal entry reference.
        :return:            A string representing the invoice.
        '''
        self.ensure_one()
        draft_name = ''
        if self.state == 'draft':
            draft_name += {
                'out_invoice': _('Draft Invoice'),
                'out_refund': _('Draft Credit Note'),
                'in_invoice': _('Draft Bill'),
                'in_refund': _('Draft Vendor Credit Note'),
                'out_receipt': _('Draft Sales Receipt'),
                'in_receipt': _('Draft Purchase Receipt'),
                'entry': _('Draft Entry'),
            }[self.move_type]
            if not self.n_name or self.n_name == '/':
                draft_name += ' (* %s)' % str(self.id)
            else:
                draft_name += ' ' + self.n_name
        return (draft_name or self.n_name) + (show_ref and self.ref and ' (%s%s)' % (self.ref[:50], '...' if len(self.ref) > 50 else '') or '')


    def _compute_new_name(self):
        for move_id in self : 
            if move_id.name and move_id.name != '/':
                # name = "inv/2023/08/0002"
                name_list = move_id.name.split('/')
                name = name_list[1] + "-" + name_list[2] + "-" + name_list[3]
                move_id.n_name = name
            else : 
                move_id.n_name = move_id.name


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    telenoc_e_invoice_tax_amount = fields.Float(string='Tax Amount', compute='_compute_tax_amount', digits='Product Price')

    @api.depends('price_subtotal', 'price_total')
    def _compute_tax_amount(self):
        for record in self:
            record.telenoc_e_invoice_tax_amount = record.price_total - record.price_subtotal
