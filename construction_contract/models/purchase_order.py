#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    contract_id = fields.Many2one(string='Construction Contract',
                                  comodel_name='project.contract',
                                  required=False, readonly=True, states={'draft': [('readonly', False)]})
    project_id = fields.Many2one(string='Project',
                                 comodel_name='project.project',
                                 required=False, readonly=True, states={'draft': [('readonly', False)]})

    stage_ids = fields.Many2many(string='Stages',
                                 comodel_name='project.task.type',
                                 # compute='_compute_stage_ids',  # get all stages from lines
                                 required=False, readonly=True, states={'draft': [('readonly', False)]})
    task_ids = fields.Many2many(string='Tasks',
                                comodel_name='project.task',
                                # compute='_compute_task_ids',  # get all tasks from lines
                                required=False, readonly=True, states={'draft': [('readonly', False)]})


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    # Set a default value and do not make it a related field (contract_id.project_id)
    # since standalone PO may be created in various business use cases.
    project_id = fields.Many2one(string='Project',
                                 comodel_name='project.project',
                                 required=False, readonly=True, states={'draft': [('readonly', False)]})

    # Not related, so a general purchase can be linked to PO Line, accommodating extra purchases
    contract_id = fields.Many2one(string='Construction Contract',
                                  comodel_name='project.contract',
                                  required=False, readonly=True, states={'draft': [('readonly', False)]})
    contract_line_id = fields.Many2many(string='Construction Contract Line',
                                        comodel_name='project.contract.line',
                                        required=False, readonly=True, states={'draft': [('readonly', False)]})

    # Reporting, extra links that may be needed in future releases
    stage_id = fields.Many2one(string='Stage',
                               comodel_name='project.task.type',
                               required=False, readonly=True, states={'draft': [('readonly', False)]})
    task_id = fields.Many2one(string='Task',
                              comodel_name='project.task',
                              required=False, readonly=True, states={'draft': [('readonly', False)]})
