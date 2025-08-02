#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.

import logging
from odoo import models, fields, api, _
from odoo.exceptions import AccessError, UserError, ValidationError
_logger = logging.getLogger(__name__)


class ProjectContractReceipt(models.Model):
    _name ='project.contract.receipt'
    _description = 'Project Contract Receipt'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']
    _order = 'date DESC, id DESC'
    _check_company_auto = True

    name = fields.Char(string='Receipt ID', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: 'New')

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date']))
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('project.receipt',
                                                                     sequence_date=seq_date) or '/'

        temp_record = self_comp.new(vals)

        if temp_record.contract_id.history_line_ids:
            total_payments = sum(line.payment_amount for line in temp_record.contract_id.history_line_ids if line.contract_stage_id.id == temp_record.contract_stage_id.id)
            total_with_current = total_payments + temp_record.payment_amount

            if temp_record.contract_type == 'cost_plus':
                if total_with_current > temp_record.stage_amount:
                    raise UserError(_("The payment amount plus the total of the previous payments cannot be greater than the stage amount"))
            elif temp_record.contract_type == 'ratio':
                if total_with_current > temp_record.percent_amount:
                    raise UserError(_("The payment amount plus the total of the previous payments cannot be greater than the stage amount"))
            else:
                if total_with_current > temp_record.unit_amount:
                    raise UserError(_("The payment amount plus the total of the previous payments cannot be greater than the stage amount"))
        else:
            if temp_record.contract_type == 'cost_plus':
                if temp_record.payment_amount > temp_record.stage_amount:
                    raise UserError(_("The payment amount cannot be greater than the stage amount"))
            elif temp_record.contract_type == 'ratio':
                if temp_record.payment_amount > temp_record.percent_amount:
                    raise UserError(_("The payment amount cannot be greater than the stage amount"))
            else:
                if temp_record.payment_amount > temp_record.unit_amount:
                    raise UserError(_("The payment amount cannot be greater than the stage amount"))

        res = super(ProjectContractReceipt, self_comp).create(vals)

        return res

    receipt_type = fields.Selection(selection=[('with_c', 'With contract'),
                                        ('without_c', 'Without contract')],
                             required=True, tracking=True, default='with_c', readonly=True, states={'draft': [('readonly', False)]})

    partner_id = fields.Many2one(comodel_name='res.partner', required=True,
                                 readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    contract_id = fields.Many2one(string='Contract', comodel_name='project.contract',
                                    readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    date_contract = fields.Date(string='Contract Date', 
                                tracking=True,
                                readonly=True,
                                related='contract_id.date_contract')

    date = fields.Datetime(string='Date', tracking=True,
                           required=True, default=fields.Date.context_today,
                           readonly=True, states={'draft': [('readonly', False)]},
                           help='Date of this receipt report.')

    date_receipt = fields.Date(string='Receipt Date', tracking=True,
                               required=True, default=fields.Date.context_today,
                               readonly=True, states={'draft': [('readonly', False)]},
                               help='Date on which the works were done, completed or received.')
    manager_approval_date = fields.Datetime(string='PM Approval Date', tracking=True,
                                            readonly=True, copy=False,
                                            help='Date on which the project manager approved this receipt.')
    manager_user_id = fields.Many2one(string='Project Manager', tracking=True,
                                      related='project_id.user_id', store=True, readonly=True)
    maintenance_approval_date = fields.Datetime(string='Maintenance Approval Date', tracking=True,
                                                readonly=True, copy=False,
                                                help='Date on which the maintenance engineer approved this receipt.')
    maintenance_user_id = fields.Many2one(related='project_id.maintenance_user_id', tracking=True,
                                          store=True, readonly=True)
    engineer_approval_date = fields.Datetime(string='Engineer Approval Date', tracking=True,
                                             readonly=True, copy=False,
                                             help='Date on which the project engineer approved this receipt.')
    engineer_user_id = fields.Many2one(related='project_id.engineer_user_id', tracking=True,
                                        store=True, readonly=True)
    ceo_approval_date = fields.Datetime(string='CEO Approval Date', tracking=True,
                                        readonly=True, copy=False,
                                        help='Date on which the CEO approved this receipt.')
    ceo_user_id = fields.Many2one(string='CEO', tracking=True,
                                  comodel_name='res.users',
                                  default=lambda self: self.company_id.ceo_user_id or self.env.company.ceo_user_id,
                                  readonly=True, required=True,
                                  help='CEO of the company is set on the Settings Configuration page.')
    approval_date = fields.Datetime(string='Approval Date', tracking=True,
                                    compute='_compute_approval_date', readonly=True, store=True,
                                    help='Date on which the receipt was fully approved by all departments.')

    @api.depends('manager_approval_date', 'maintenance_approval_date',
                 'engineer_approval_date', 'ceo_approval_date')
    def _compute_approval_date(self):
        for receipt in self:
            if not receipt.approval_date and all([receipt.manager_approval_date, receipt.maintenance_approval_date,
                    receipt.engineer_approval_date, receipt.ceo_approval_date]):
                receipt.approval_date = fields.Datetime.now()
            else:
                receipt.approval_date = False

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update the domain of contract_id based on the selected partner.

        """
        if self.partner_id:
            contract_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'progress'),
            ]
            return {'domain': {'contract_id': contract_domain}}
        else:
            return {'domain': {'contract_id': []}}

    @api.onchange('contract_id')
    def _onchange_contract_id(self):
        if self.contract_id:
            self.project_id = self.contract_id.project_id
        else:
            self.project_id = False

    contract_stage_id = fields.Many2one(string='Contract Stage', tracking=True,
                                        comodel_name='project.contract.stage',
                                        readonly=True, states={'draft': [('readonly', False)]})
    percent = fields.Float(string='Payment Percent', tracking=True,
                            comodel_name='project.contract.stage',
                            related="contract_stage_id.percent")
    percent_amount = fields.Float(string='Percent Amount', tracking=True,
                            comodel_name='project.contract.stage',
                            related="contract_stage_id.percent_amount")
    progress = fields.Float(string='Progress',
                            store=True)
    actual_progress = fields.Float(string='Actual progress', tracking=True,
                                comodel_name='project.contract.stage',
                                # related="contract_stage_id.actual_progress", 
                                readonly=True, states={'draft': [('readonly', False)]})
    unit = fields.Float(string='Num of Units/ Meters', tracking=True,
                            comodel_name='project.contract.stage',
                            related="contract_stage_id.unit",
                            readonly=True)
    unit_amount = fields.Float(string='Units/ Meters Amount', tracking=True,
                            comodel_name='project.contract.stage',
                            related="contract_stage_id.unit_amount",
                            readonly=True)
    actual_unit = fields.Float(string='Actual Num of Units/ Meters', tracking=True,
                                comodel_name='project.contract.stage',
                                # related="contract_stage_id.actual_unit", 
                                readonly=True, states={'draft': [('readonly', False)]})
    stage_amount = fields.Float(string="Stage amount", tracking=True,
                                comodel_name='project.contract.stage',
                                related="contract_stage_id.stage_amount", 
                                readonly=True)
    stage_state = fields.Selection(string='Status',
                             selection=[('draft', 'Draft'),
                                        ('waiting', 'Waiting Approval'),
                                        ('progress', 'In Progress'),
                                        ('done', 'Closed'),
                                        ('cancel', 'Cancelled')],
                             related="contract_stage_id.state")
    date_start = fields.Date(string='Start Date',
                             readonly=True, related="contract_stage_id.date_start")
    date_end = fields.Date(string='End Date',
                           readonly=True, related="contract_stage_id.date_end")
    payment_amount = fields.Float(string="Payment amount", tracking=True)
    amount = fields.Float(string="Payment amount", tracking=True)
    contract_type = fields.Selection(string='Contract Type',
                                    readonly=True, 
                                    related="contract_id.contract_type")
    # contract_line_id = fields.Many2one(string='Contract Line',
    #                                    comodel_name='project.contract.line',
    #                                    required=True, readonly=True, states={'draft': [('readonly', False)]})
    project_id = fields.Many2one(string='Project', tracking=True,
                                 comodel_name='project.project',
                                 related='contract_id.project_id',
                                 readonly=True, states={'draft': [('readonly', False)]})
    task_id = fields.Many2one(string='Task', tracking=True,
                              comodel_name='project.task',
                              domain="[('project_id', '=', project_id)]",
                              readonly=True, states={'draft': [('readonly', False)]})
    project_stage_id = fields.Many2one(string='Project Stage', tracking=True,
                                       comodel_name='project.task.type',
                                       domain="[('project_ids', '=', project_id)]",
                                       readonly=True, states={'draft': [('readonly', False)]})
    project = fields.Many2one(string='Project', tracking=True,
                                 comodel_name='project.project',
                                 readonly=True, states={'draft': [('readonly', False)]})
    task = fields.Many2one(string='Task', tracking=True,
                              comodel_name='project.task',
                              domain="[('project_id', '=', project)]",
                              readonly=True, states={'draft': [('readonly', False)]})
    stage = fields.Many2one(string='Project Stage', tracking=True,
                                comodel_name='project.task.type',
                                domain="[('project_ids', '=', project)]",
                                readonly=True, states={'draft': [('readonly', False)]})
    description = fields.Html(string='Receipt Description', tracking=True,
                              required=True, readonly=True, states={'draft': [('readonly', False)]},
                              default=lambda self: self.env.company.construction_receipt_body or '',
                              translate=True)
    waiting_approval = fields.Boolean(string='Waiting Approval', tracking=True,
                                      default=False, readonly=True, copy=False,
                                      help='Technical fields used to track the approval process.')
    is_cancelled = fields.Boolean(string='Cancelled', tracking=True,
                                  default=False, readonly=True, copy=False,
                                  help='Technical fields used to track the cancellation process.')
    cancel_reason = fields.Text(string='Cancellation Notes', readonly=True, tracking=True)
    cancel_reason_id = fields.Many2one(string='Cancel Reason', tracking=True,
                                       comodel_name='project.construction.cancel.reason', readonly=True)
    cancel_date = fields.Datetime(string='Cancel/Reject Date', readonly=True, copy=False, tracking=True)
    state = fields.Selection(string='Status',
                             selection=[('draft', 'Draft'),
                                        ('waiting', 'Project manager approval'),
                                        ('fm_approved', 'Finance manager approval'),
                                        ('gm_approved', 'General manager approval'),
                                        ('approved', 'Approved'),
                                        ('reject', 'Rejected'),
                                        ('cancel', 'Cancelled')],
                             compute='_compute_state', readonly=True, store=True,
                             required=True, tracking=True, default='draft')

    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    contractor_ids = fields.Many2many('cash.order', string='Cash Order', tracking=True)

    @api.onchange('actual_progress','percent','unit','actual_unit')
    def _compute_progress(self):
        ''' a function that compute the progress based on the actual progress

        '''
        for rec in self:
            if rec.actual_progress:
                result = rec.actual_progress / rec.percent
                rec.progress =  result * 100
            if rec.actual_unit:
                result = rec.actual_unit / rec.unit
                rec.progress =  result * 100

    @api.onchange('contract_id')
    def _onchange_contract_stage_id(self):
        """Update the domain of contract_stage_id based on the selected contract.

        """
        domain = [('partner_id', '=', self.partner_id.id),
                  ('contract_id', '=', self.contract_id.id),
                  ('state', 'not in', ['done', 'cancel'])]
        return {'domain': {'contract_stage_id': domain}}

    def set_confirm(self):
        _logger.info('set_confirm method called for record: %s', self.id)
        # for receipt in self:
            # receipt.write({'waiting': True})
        self.write({'state': 'waiting'})


    def action_wait(self):
        for receipt in self:
            receipt.write({'manager_approval_date': fields.Datetime.now()})
        self.write({
            'state': 'fm_approved',
            'name': 'CRE/0'+str(self.id),
        })


    def fm_approve(self):
        for receipt in self:
            receipt.write({'maintenance_approval_date': fields.Datetime.now()})
        self.contract_stage_id.write({'actual_progress': self.actual_progress,
                                        'actual_unit': self.actual_unit,
                                        'progress': self.progress,})
        return self.write({'state': 'gm_approved'})


    def gm_approve(self):
        for receipt in self:
            receipt.write({'engineer_approval_date': fields.Datetime.now()})
        if self.receipt_type == 'with_c':
            contractor = self.env['cash.order'].sudo().create({
                'disc':self.name + '\n' + self.project_id.name + '\n' + self.description,
                'partner_id':self.partner_id.id,
                'date':self.maintenance_approval_date,
                'project_id':self.project_id.id,
                'exchange_type_id': self.exchange_type_id.id,
                'amount':self.payment_amount,})

            self.contract_stage_id.write({
                     'receipt_id': receipt.id,
                     'payment_id': contractor.id,
                 })

            if self.contract_id.history_line_ids:
                total_payments = sum(line.payment_amount for line in self.contract_id.history_line_ids if line.contract_stage_id.id == self.contract_stage_id.id)
                total_with_current = total_payments + self.payment_amount

                if self.contract_type == 'cost_plus':
                    if total_with_current >= self.stage_amount:
                        self.contract_stage_id.write({'state': 'done'})
                    else:
                        self.contract_stage_id.write({'state': 'progress'})

                elif self.contract_type == 'ratio':
                    if total_with_current >= self.percent_amount:
                        self.contract_stage_id.write({'state': 'done'})
                    else:
                        self.contract_stage_id.write({'state': 'progress'})
                else:
                    if total_with_current >= self.unit_amount:
                        self.contract_stage_id.write({'state': 'done'})
                    else:
                        self.contract_stage_id.write({'state': 'progress'})
            else:
                if self.contract_type == 'cost_plus':
                    if self.payment_amount >= self.stage_amount:
                        self.contract_stage_id.write({'state': 'done'})
                    else:
                        self.contract_stage_id.write({'state': 'progress'})

                elif self.contract_type == 'ratio':
                    if self.payment_amount >= self.percent_amount:
                        self.contract_stage_id.write({'state': 'done'})
                    else:
                        self.contract_stage_id.write({'state': 'progress'})
                else:
                    if self.payment_amount >= self.unit_amount:
                        self.contract_stage_id.write({'state': 'done'})
                    else:
                        self.contract_stage_id.write({'state': 'progress'})
        else:
            contractor = self.env['cash.order'].sudo().create({
                'disc': self.name + '\n' + self.project.name + '\n' + self.description,
                'partner_id':self.partner_id.id,
                'date':self.maintenance_approval_date,
                'project_id':self.project_id.id,
                'exchange_type_id': self.exchange_type_id.id,
                'amount':self.amount,})
        self.contractor_ids = [(4,contractor.id)]
        self.update_history()
        return self.write({'state': 'approved'})

    def update_history(self):
        self.contract_id.write({
            'history_line_ids': [(0, 0, {
                'name': self.name,
                'date': self.date,
                'contract_stage_id': self.contract_stage_id.id,
                'percent': self.percent,
                'percent_amount': self.percent_amount,
                'progress': self.progress,
                'actual_progress': self.actual_progress,
                'unit': self.unit,
                'unit_amount': self.unit_amount,
                'actual_unit': self.actual_unit,
                'percent': self.percent,
                'stage_amount': self.stage_amount,
                'payment_amount': self.payment_amount,
                'state': self.contract_stage_id.state,
                'contract_type': self.contract_type,
            })]
        })

    def open_cash_order(self):
        domain = [ ('id', 'in',self.contractor_ids.ids)]
        return {
          'name': _('Cash Order'),           
          'domain': domain,          
          'res_model': 'cash.order', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form',
          'help': _('''<p class="oe_view_nocontent_create">
           
                                    Attach
    documents of your employee.</p>'''),
         'limit': 80,
         }

    def set_cancel(self):
        self.ensure_one()
        if self.state not in ['draft', 'waiting', 'fm_approved', 'gm_approved']:
            raise UserError(_('You can only cancel a receipt that is in draft or waiting approval states.'))
        return {
            'name': _('Cancel Receipt'),
            'view_mode': 'form',
            'res_model': 'construction.reject.wizard',
            'view_id': self.env.ref('construction_contract.construction_contract_reject_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_receipt_id': self.id, 'reject': False, 'field': 'receipt_id'},
            'target': 'new'
        }

    def set_reject(self):
        self.ensure_one()
        if self.state not in ['waiting', 'fm_approved','gm_approved']:
            raise UserError(_('You can only reject a receipt that is waiting for approval.'))
        return {
            'name': _('Cancel Receipt'),
            'view_mode': 'form',
            'res_model': 'construction.reject.wizard',
            'view_id': self.env.ref('construction_contract.construction_contract_reject_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_receipt_id': self.id, 'reject': True, 'field': 'receipt_id'},
            'target': 'new'
        }


    @api.depends('maintenance_approval_date', 'engineer_approval_date', 'manager_approval_date',
                 'ceo_approval_date', 'waiting_approval', 'is_cancelled')
    def _compute_state(self):
        for receipt in self:
            if receipt.is_cancelled is True:
                receipt.state = 'cancel'
            elif receipt.is_cancelled is False and not any([receipt.maintenance_approval_date,
                                                            receipt.engineer_approval_date,
                                                            receipt.manager_approval_date, receipt.ceo_approval_date]):
                receipt.state = 'waiting'

            elif receipt.is_cancelled is False and all([receipt.maintenance_approval_date,
                                                        receipt.engineer_approval_date,
                                                        receipt.manager_approval_date, receipt.ceo_approval_date]):
                receipt.state = 'approved'
                receipt.update({'waiting_approval': False, 'approval_date': fields.Datetime.now()})
            else:
                receipt.state = 'draft'

    company_id = fields.Many2one(string='Company',
                                 comodel_name='res.company',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.company)

    user_id = fields.Many2one(string='Responsible',
                              comodel_name='res.users',
                              required=True, readonly=True, states={'draft': [('readonly', False)]},
                              default=lambda self: self.env.user)

    def unlink(self):
        for settlement in self:
            if settlement.state not in ['draft','waiting']:
                raise UserError(_('You can only delete draft receipts. Cancel it instead.'))
        return super(ProjectContractReceipt, self).unlink()


class ProjectContractFinalReceipt(models.Model):
    _name ='project.contract.final.receipt'
    _description = 'Project Contract Receipt'
    _inherit = ['mail.thread', 'mail.activity.mixin', 'portal.mixin']

    name = fields.Char(string='Receipt ID', required=True, copy=False, readonly=True,
                       index=True, default=lambda self: 'New')
    partner_id = fields.Many2one(string='Contractor', comodel_name='res.partner', required=True, tracking=True,
                                 readonly=True, states={'draft': [('readonly', False)]})
    contract_id = fields.Many2one(string='Contract', comodel_name='project.contract', tracking=True,
                                    readonly=True, states={'draft': [('readonly', False)]})
    contract_type = fields.Selection(string='Contract Type',
                                    readonly=True, 
                                    related="contract_id.contract_type")
    project_id = fields.Many2one(string='Project', tracking=True,
                                 comodel_name='project.project',
                                 related='contract_id.project_id',
                                 readonly=True, states={'draft': [('readonly', False)]})
    date = fields.Datetime(string='Date', tracking=True,
                           required=True, default=fields.Date.context_today,
                           readonly=True, states={'draft': [('readonly', False)]},
                           help='Date of this receipt report.')
    manager_user_id = fields.Many2one(string='Project Manager', tracking=True,
                                      related='project_id.user_id', store=True, readonly=True)
    maintenance_user_id = fields.Many2one(related='project_id.maintenance_user_id',
                                          store=True, readonly=True)
    engineer_user_id = fields.Many2one(related='project_id.engineer_user_id',
                                        store=True, readonly=True, tracking=True)
    cancel_reason = fields.Text(string='Cancellation Notes', readonly=True, tracking=True)
    cancel_reason_id = fields.Many2one(string='Cancel Reason',
                                       comodel_name='project.construction.cancel.reason', readonly=True, tracking=True)
    cancel_date = fields.Datetime(string='Cancel/Reject Date', readonly=True, copy=False)
    ten_percentage = fields.Float(related='contract_id.ten_percentage', tracking=True, digits=(16, 2), string='10% Amount', readonly=True)
    ten_percent = fields.Float(related='contract_id.ten_percent', tracking=True, digits=(16, 2), string='10% Amount', readonly=True)
    contractor_ids = fields.Many2many('cash.order', string='Cash Order', tracking=True)
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    state = fields.Selection(string='Status',
                             selection=[('draft', 'Draft'),
                                        ('maintenance', 'Maintenance approval'),
                                        ('pm_approved', 'Project manager approval'),
                                        ('fm_approved', 'Finance manager approval'),
                                        ('gm_approved', 'General manager approval'),
                                        ('approved', 'Approved'),
                                        ('reject', 'Rejected'),
                                        ('cancel', 'Cancelled')],
                             required=True, tracking=True, default='draft')
    change = fields.Boolean(string="Change the 10% amount?", tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    reason = fields.Char(string="Reason", readonly=True, states={'draft': [('readonly', False)]})
    change_amount = fields.Float(string="Amount", tracking=True)
    subtotal = fields.Float(compute="_compute_subtotal", digits=(16, 2), string="Subtotal amount", readonly=True, tracking=True)

    @api.depends('ten_percentage', 'change', 'change_amount')
    def _compute_subtotal(self):
        '''Compute the final receipt subtotal based on various conditions.

        '''
        for rec in self:
            if rec.change:
                if rec.ten_percentage > 0:
                    rec.subtotal = rec.ten_percentage + rec.change_amount
                else:
                    rec.subtotal = rec.ten_percent + rec.change_amount
            else:
                if rec.ten_percentage > 0:
                    rec.subtotal = rec.ten_percentage
                else:
                    rec.subtotal = rec.ten_percent

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Update the domain of contract_id based on the selected partner.

        """
        if self.partner_id:
            contract_domain = [
                ('partner_id', '=', self.partner_id.id),
                ('state', '=', 'progress'),
            ]
            return {'domain': {'contract_id': contract_domain}}
        else:
            return {'domain': {'contract_id': []}}


    def set_confirm(self):
        self.write({'state': 'maintenance'})


    def action_maintenance(self):
        self.write({
            'state': 'pm_approved',
            'name': 'FR/0'+str(self.id),
        })


    def pm_approve(self):
        return self.write({'state': 'fm_approved'})

    def fm_approved(self):
        return self.write({'state': 'gm_approved'})


    def gm_approve(self):
        if self.change:
            if self.ten_percentage > 0:
                self.subtotal = self.ten_percentage + self.change_amount
            else:
                self.subtotal = self.ten_percent + self.change_amount

        else:
            if self.contract_type in ['cost_plus', 'ratio']:
                self.subtotal = self.ten_percentage
            else:
                self.subtotal = self.ten_percent

        contractor = self.env['cash.order'].sudo().create({
            'disc':self.name + '\n' + self.project_id.name,
            'partner_id':self.partner_id.id,
            'date':self.date,
            'project_id':self.project_id.id,
            'exchange_type_id': self.exchange_type_id.id,
            'amount':self.subtotal,})
        self.contractor_ids = [(4,contractor.id)]
        self.contract_id.write({'state': 'done'})
        return self.write({'state': 'approved'})

    def open_cash_order(self):
        domain = [ ('id', 'in',self.contractor_ids.ids)]
        return {
          'name': _('Cash Order'),           
          'domain': domain,          
          'res_model': 'cash.order', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'tree,form',
          'help': _('''<p class="oe_view_nocontent_create">
           
                                    Attach
    documents of your employee.</p>'''),
         'limit': 80,
         }


    def set_cancel(self):
        self.ensure_one()
        if self.state not in ['draft', 'maintenance', 'pm_approved', 'gm_approved']:
            raise UserError(_('You can only cancel a receipt that is in draft or waiting maintenance approval states.'))
        return {
            'name': _('Cancel Receipt'),
            'view_mode': 'form',
            'res_model': 'construction.reject.wizard',
            'view_id': self.env.ref('construction_contract.construction_contract_reject_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_receipt_id': self.id, 'reject': False, 'field': 'receipt_id'},
            'target': 'new'
        }

    def set_reject(self):
        self.ensure_one()
        if self.state not in ['maintenance', 'pm_approved','gm_approved']:
            raise UserError(_('You can only reject a receipt that is waiting for maintenance approval.'))
        return {
            'name': _('Cancel Receipt'),
            'view_mode': 'form',
            'res_model': 'construction.reject.wizard',
            'view_id': self.env.ref('construction_contract.construction_contract_reject_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_receipt_id': self.id, 'reject': True, 'field': 'receipt_id'},
            'target': 'new'
        }
