#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _


class Project(models.Model):
    _inherit = 'project.project'

    contract_ids = fields.One2many(string='Contracts', tracking=True,
                                   comodel_name='project.contract',
                                   inverse_name='project_id')
    contract_count = fields.Integer(string='Contracts Count', tracking=True,
                                    compute='_compute_contract_count', store=True)

    @api.depends('contract_ids')
    def _compute_contract_count(self):
        for project in self:
            project.contract_count = len(project.contract_ids)

    maintenance_user_id = fields.Many2one(string='Maintenance User',
                                          comodel_name='res.users',
                                          required=False,
                                          tracking=True)
    maintenance_partner_id = fields.Many2one(string='Maintenance Contact',
                                             comodel_name='res.partner',
                                             required=False,
                                             tracking=True)
    engineer_user_id = fields.Many2one(string='Engineer User',
                                       comodel_name='res.users',
                                       required=False,
                                       tracking=True)
    ceo_user_id = fields.Many2one(string='CEO User', tracking=True,
                                  comodel_name='res.users',
                                  default=lambda self: self.company_id.ceo_user_id.id or self.env.company.ceo_user_id.id or False)


class ProjectTask(models.Model):
    _inherit = 'project.task'

    contract_ids = fields.Many2many(string='Tasks',
                                    comodel_name='project.contract',
                                    relation='project_contract_task_rel',
                                    column1='task_id',
                                    column2='contract_id')

class ProjectStage(models.Model):
    _inherit = 'project.task.type'

    contract_ids = fields.Many2many(string='Contracts',
                                    comodel_name='project.contract',
                                    relation='project_contract_stage_rel',
                                    column1='stage_id',
                                    column2='contract_id')