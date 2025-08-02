# -*- coding: utf-8 -*-
##############################################################################
#
#    
#    
#
##############################################################################
from odoo import api, fields, models,_

class JournalEntryWizard(models.TransientModel):
    _name = "journal.entry.wizard"
    _description = "Journal Entry Wizard Report"

    report_type = fields.Selection(
        [
            ('pdf', 'PDF'),
            ("xlsx", "Excel")],
        required=True, default='pdf',string="Select Report Type",
        help='The type of the report that will be rendered, each one having its own rendering method.'
             'Excel will print Excel Report'
             'PDF will print PDF Report')
    landscape = fields.Boolean(string="Landscape")

    def print_report(self):
        move = self.env['account.move'].browse(self.env.context.get('active_id'))
        data = {
            'move': move,
            'model': 'account.move',
        }
        if self.report_type == 'xlsx':
            return self.env.ref('account_reports_custom.action_report_journal_entries_xlsx').report_action(move, data=data)
        else:
            return self.env.ref('account_reports_custom.action_report_journal_entries_pdf').with_context(
            landscape=self.landscape).report_action(move, data=data)

