#  Hash Information Technology (c) 2024. All rights reserved.
#  See LICENSE file for full copyright and licensing details.


from odoo import models, fields, api, _
from odoo.tools.misc import formatLang, get_lang, format_amount
from odoo.exceptions import AccessError, UserError, ValidationError
from odoo.tools.float_utils import float_is_zero, float_compare


class ProjectContract(models.Model):
    _name = 'project.contract'
    _description = 'Project Contract'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'date_contract desc, sequence desc'
    _check_company_auto = True

    active = fields.Boolean(default=True, tracking=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)
    name = fields.Char(string='Contract Number', required=True, copy=False, readonly=True,
                       states={'draft': [('readonly', False)]}, index=True,
                       default=lambda self: 'New', tracking=True)

    @api.model
    def create(self, vals):
        company_id = vals.get('company_id', self.default_get(['company_id'])['company_id'])
        self_comp = self.with_company(company_id)
        if vals.get('name', 'New') == 'New':
            seq_date = None
            if 'date_contract' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['date_contract']))
            vals['name'] = self_comp.env['ir.sequence'].next_by_code('project.contract', sequence_date=seq_date) or '/'
        res = super(ProjectContract, self_comp).create(vals)

        return res

    def unlink(self):
        for contract in self:
            if not contract.state == 'cancel':
                raise UserError(_('In order to delete a contract, you must cancel it first.'))
        return super(ProjectContract, self).unlink()

    def default_currency(self):
        return self.env.user.company_id.currency_id

    date_contract = fields.Date(string='Contract Date', tracking=True,
                                required=True, readonly=True, states={'draft': [('readonly', False)]},
                                default=lambda self: fields.Date.context_today(self))
    date_start = fields.Date(string='Start Date', tracking=True, required=True, readonly=True, states={'draft': [('readonly', False)]},
                             default=lambda self: fields.Date.context_today(self))
    date_end = fields.Date(string='End Date',
                           required=True, tracking=True, readonly=True, states={'draft': [('readonly', False)]},
                           default=lambda self: fields.Date.context_today(self))
    date_approve_project = fields.Datetime(string='PM Approval', readonly=True, copy=False, tracking=True)
    date_approve_admin = fields.Datetime(string='Admin Approval', readonly=True, copy=False, tracking=True)

    contract_type = fields.Selection(string='Contract Type',
                                     selection=[('cost_plus', 'Fixed amount/ Direct'),
                                                ('meter', 'Meter-based'),
                                                ('unit', 'Unit-based'),
                                                ('ratio', 'Ratio-based')],
                                     required=True, tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    currency_id = fields.Many2one('res.currency', string='Currency',default=default_currency,required=True, readonly=True, states={
        'draft': [('readonly', False)]})
    amount = fields.Monetary('Contract Amount', tracking=True, readonly=True, states={
        'draft': [('readonly', False)]})
    ten_percentage = fields.Float(compute="_amount_all", digits=(16, 2), string='10% Amount', readonly=True, store=True)
    remain_amount = fields.Float(compute="_amount_all", digits=(16, 2), string='Remain amount', readonly=True)
    unit_price = fields.Float(string="Unit/ Meter price", tracking=True)
    total = fields.Float(string="Total Unit/ Meter", tracking=True)
    total_price = fields.Float(compute="_amount_all", digits=(16, 2), string="amount", readonly=True, tracking=True)
    ten_percent = fields.Float(compute="_amount_all", digits=(16, 2), string="10% amount", readonly=True, tracking=True)
    price = fields.Float(compute="_amount_all", digits=(16, 2), string="Total amount", readonly=True, tracking=True)
    discount = fields.Boolean(string="Enable discount amount?", tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    discount_type = fields.Selection(string="Discount type",
                                        selection=[('fix','Fixed'),
                                                    ('percent','Percent')],
                                        default='fix', tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    discount_amount = fields.Float(string="Discount amount", tracking=True, readonly=True, states={'draft': [('readonly', False)]})
    discount_subtotal = fields.Float(compute="_compute_subtotal", digits=(16, 2), string="Subtotal amount", readonly=True, tracking=True)
    contract_template_id = fields.Many2one(string='Contract Template', tracking=True,
                                           comodel_name='project.contract.template',
                                           readonly=True, states={'draft': [('readonly', False)]})
    project_stage_ids = fields.Many2many(string='Project Stages', tracking=True,
                                         comodel_name='project.task.type',
                                         relation='project_contract_stage_rel',
                                         column1='contract_id',
                                         column2='stage_id',
                                         compute='_compute_stages_tasks')  # get all stages from lines
    task_ids = fields.Many2many(string='Tasks', tracking=True,
                                comodel_name='project.task',
                                relation='project_contract_task_rel',
                                column1='contract_id',
                                column2='task_id',
                                compute='_compute_stages_tasks')  # get all tasks from lines
    history_line_ids = fields.One2many('payment.history.line', 'history_line_id', readonly=True)    

    @api.onchange('contract_type')
    def _onchange_contract_type(self):
        '''Reset fields when changing contract type

        '''
        for rec in self:
            if rec.contract_type == 'unit_base':
                rec.amount = 0.0
            elif rec.contract_type == 'fixed':
                rec.unit_price = 0.0
                rec.total = 0.0

    @api.onchange('amount','unit_price','total')
    def _amount_all(self):
        ''' a function that calculates the 10 percent discount and the remain

        '''
        for rec in self:
            if rec.contract_type in ['cost_plus', 'ratio']:
                rec.ten_percentage = rec.amount / 10 if rec.amount else 0
                rec.remain_amount = rec.amount - rec.ten_percentage
                rec.total_price = rec.remain_amount
                rec.ten_percent = 0
                rec.price = rec.remain_amount
            else:
                rec.total_price = rec.unit_price * rec.total if rec.total else 0
                rec.ten_percent = rec.total_price / 10 if rec.total_price else 0
                rec.price = rec.total_price - rec.ten_percent
                rec.ten_percentage = 0
                rec.remain_amount = rec.amount if rec.amount else 0
        

    @api.depends('amount', 'contract_type', 'discount' , 'price', 'discount_amount')
    def _compute_subtotal(self):
        '''Compute the contract subtotal based on various conditions.

        '''
        for rec in self:
            if rec.discount:
                if rec.discount_type == 'fix':
                    if rec.contract_type in ['cost_plus', 'ratio']:
                        rec.discount_subtotal = rec.remain_amount - rec.discount_amount
                    else:
                        rec.discount_subtotal = rec.price - rec.discount_amount
                else:
                    if rec.contract_type in ['cost_plus', 'ratio']:
                        result = rec.remain_amount / rec.discount_amount if rec.discount_amount > 0 else 0
                        rec.discount_subtotal = rec.remain_amount - result
                    else:
                        result = rec.price / rec.discount_amount if rec.discount_amount > 0 else 0
                        rec.discount_subtotal = rec.price - result
            else:
                # Handle case without discount
                rec.discount_subtotal = rec.remain_amount

    @api.depends('line_ids', 'line_ids.project_stage_id', 'line_ids.task_id')
    def _compute_stages_tasks(self):
        for contract in self:
            contract.project_stage_ids = contract.line_ids.mapped('project_stage_id')
            contract.task_ids = contract.line_ids.mapped('task_id')

    @api.onchange('contract_template_id')
    def _onchange_contract_template_id(self):
        """
        Update contract clauses from selected contract template, and reset the template to False
        Clauses are used in printed contract reports.
        """
        for contract in self:
            if not contract.contract_template_id:
                continue

            # This will accumulate clauses from the template and the contract itself.
            # Check UX feedback to see if this is the desired behavior.
            contract.clause_ids = [(0, 0, {
                'name': clause.name,
                'content': clause.content,
                'sequence': clause.sequence,
            }) for clause in contract.contract_template_id.clause_ids.sorted(key=lambda l: l.sequence)]

            # Reset the template to False
            contract.contract_template_id = False


    clause_ids = fields.One2many(string='Clauses', tracking=True,
                                 comodel_name='project.contract.clause',
                                 inverse_name='contract_id',
                                 readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    partner_id = fields.Many2one(string='Contractor', comodel_name='res.partner',
                                 required=True, tracking=True, readonly=True, states={'draft': [('readonly', False)]})

    # Implement more functionality in future releases. Currently used for information purposes only.
    partner_role = fields.Selection(string='Partner Role', tracking=True,
                                    selection=[('subcontractor', 'Subcontractor'),
                                               # ('contractor', 'Contractor'),
                                               # ('supplier', 'Supplier'),  # same as subcontract, service, products, etc.
                                               ('consultant', 'Consultant'),  # Engineer, Architect, etc.
                                               # ('client', 'Client'),
                                               ('other', 'Other')],  # Everything else
                                    required=True, readonly=True, states={'draft': [('readonly', False)]})

    # Implement in a future release to manage extra or additional works contracted separately
    # parent_id = fields.Many2one(string='Parent Contract',
    #                             comodel_name='project.contract')
    # child_ids = fields.One2many(string='Subcontracts',
    #                             comodel_name='project.contract',
    #                             inverse_name='parent_id')

    currency_id = fields.Many2one(related='partner_id.property_purchase_currency_id', store=True, readonly=True)

    # Commented out, and let purchases & invoices control it.
    # Implement when taxes are confirmed to be used in contracts.
    # fiscal_position_id = fields.Many2one(string='Fiscal Position',
    #                                      comodel_name='account.fiscal.position',
    #                                      domain="[('company_id', '=', company_id)]", check_company=True,
    #                                      help='Fiscal positions are used to adapt taxes and accounts for particular '
    #                                           'customers or contracts and their invoices.\n'
    #                                           'The default value comes from the customer.')


    project_id = fields.Many2one(string='Project', tracking=True,
                                 comodel_name='project.project',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]})
    analytic_account_id = fields.Many2one(related='project_id.analytic_account_id', store=True, readonly=True)
    user_id = fields.Many2one(string='Project Manager',
                              comodel_name='res.users',
                              required=True, default=lambda self: self.env.user, index=True)
    company_id = fields.Many2one(string='Company',
                                 comodel_name='res.company',
                                 required=True, readonly=True, states={'draft': [('readonly', False)]},
                                 default=lambda self: self.env.company, index=True)

    contract_stage_ids = fields.One2many(string='Stages',
                                         comodel_name='project.contract.stage',
                                         inverse_name='contract_id',
                                         readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    line_ids = fields.One2many(string='Contract Lines',
                               comodel_name='project.contract.line',
                               inverse_name='contract_id',
                               readonly=True, states={'draft': [('readonly', False)]}, copy=True)

    amount_total = fields.Monetary(string='Total Amount',
                                   compute='_compute_amount_all', store=True, readonly=True,
                                   help='Total amount of the contract.')
    amount_subtotal = fields.Monetary(string='Subtotal',
                                      compute='_compute_amount_all', store=True, readonly=True,
                                      help='Total amount without taxes.')
    amount_tax = fields.Monetary(string='Taxes', tracking=True,
                                 compute='_compute_amount_all', store=True, readonly=True,
                                 help='Total amount of the taxes.')

    @api.depends('line_ids.price_total')
    def _compute_amount_all(self):
        """
        Method to compute total contract amounts based on lines' amounts
        """
        for contract in self:
            amount_total = amount_subtotal = amount_tax = 0.0
            for line in contract.line_ids:
                # Trigger line re-computation
                line._compute_line_amounts()
                # Sum the amounts
                amount_total += line.price_total
                amount_subtotal += line.price_subtotal
                amount_tax += line.price_tax
            # Update the values on the contract
            contract.update({
                'amount_tax': amount_tax,
                'amount_subtotal': amount_subtotal,
                'amount_total': amount_total,
            })

    cancel_reason_id = fields.Many2one(string='Cancellation Reason',
                                       comodel_name='project.construction.cancel.reason',
                                       readonly=True, copy=False, tracking=True)
    cancel_reason = fields.Text(string='Cancellation Notes',
                                readonly=True,
                                # The wizard will write the reason notes here.
                                # states={'cancel': [('readonly', False)],
                                #         'reject': [('readonly', False)]},
                                copy=False, tracking=True)
    cancel_date = fields.Datetime(string='Cancel/Reject Date', readonly=True, copy=False)
    state = fields.Selection(string='Status',
                             selection=[('draft', 'Draft'),
                                        ('waiting', 'Waiting Approval'),
                                        ('pm_approval', 'PM Approved'),
                                        ('admin_approval', 'CEO Approved'),
                                        ('progress', 'In Progress'),
                                        ('done', 'Closed'),
                                        ('reject', 'Rejected'),
                                        ('cancel', 'Cancelled')],
                             required=True, readonly=True, default='draft',
                             copy=False, tracking=True)

    def set_confirm(self):
        for contract in self:
            if contract.state == 'draft':
                if contract.contract_type == 'cost_plus':
                    total = sum(line.stage_amount for line in contract.contract_stage_ids)

                if contract.contract_type == 'ratio':
                    total = sum(line.percent_amount for line in contract.contract_stage_ids)

                if contract.contract_type in ['unit', 'meter']:
                    total = sum(line.unit_amount for line in contract.contract_stage_ids)

                if contract.contract_type in ['cost_plus', 'ratio']:
                    target_amount = contract.discount_subtotal if contract.discount else contract.remain_amount
                else:
                    target_amount = contract.discount_subtotal if contract.discount else contract.price

                if float_compare(total, target_amount, precision_digits=2) != 0:
                    raise UserError(_("Invalid amount. Please ensure that the total of scheduled payments matches the contract amount after discount."))

                contract.state = 'waiting'
            else:
                raise UserError(_('You can only confirm draft contracts.'))

    def approve_pm(self):
        for contract in self:
            if contract.state == 'waiting':
                contract.write({'state': 'pm_approval', 'date_approve_project': fields.Datetime.now()})
            else:
                raise UserError(_('PM already approved this contract.'))

    def approve_admin(self):
        for contract in self:
            if contract.state == 'pm_approval':
                contract.write({'state': 'admin_approval', 'date_approve_admin': fields.Datetime.now()})
            else:
                raise UserError(_('CEO already approved this contract.'))

    def action_progress(self):
        if self.state == 'admin_approval':
            return self.write({'state': 'progress'})

    def action_done(self):
        if self.state == 'progress':
            return self.write({'state': 'done'})

    def set_reject(self):
        self.ensure_one()
        if self.state in ['draft', 'cancel', 'done']:
            raise UserError(_('You cannot reject an already approved or closed or open contracts.'))
        return {
            'name': _('Reject Contract'),
            'view_mode': 'form',
            'res_model': 'construction.reject.wizard',
            'view_id': self.env.ref('construction_contract.construction_contract_reject_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_contract_id': self.id, 'reject': True, 'field': 'contract_id'},
            'target': 'new'
        }

    def set_cancel(self):
        self.ensure_one()
        if self.state in ['done', 'reject']:
            raise UserError(_('You cannot cancel a closed or rejected or already cancelled contracts.'))
        return {
            'name': _('Cancel Contract'),
            'view_mode': 'form',
            'res_model': 'construction.reject.wizard',
            'view_id': self.env.ref('construction_contract.construction_contract_reject_form').id,
            'type': 'ir.actions.act_window',
            'context': {'default_contract_id': self.id, 'reject': False, 'field': 'contract_id'},
            'target': 'new'
        }

    def set_to_draft(self):
        if self.state == 'cancel':
            return self.write({'state': 'draft'})


class ProjectContractLine(models.Model):
    _name = 'project.contract.line'
    _description = 'Project Contract Line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    _check_company_auto = True

    name = fields.Char(string='Line Name', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1)
    display_type = fields.Selection(selection=[('line_section', 'Section'),
                                               ('line_note', 'Note')],
                                    default=False, help="Technical field for UX purpose.")
    contract_id = fields.Many2one(string='Contract',
                                  comodel_name='project.contract',
                                  required=True, ondelete='cascade', index=True, copy=False)
    contract_type = fields.Selection(string='Contract Type', 
                                    tracking=True, 
                                    readonly=True,
                                    related='contract_id.contract_type')
    project_id = fields.Many2one(related='contract_id.project_id', store=True, readonly=True)
    contract_stage_id = fields.Many2one(string='Contract Stage',
                                        comodel_name='project.contract.stage',
                                        required=False, ondelete='set null', copy=False)
    project_stage_id = fields.Many2one(string='Project Stage',
                                       comodel_name='project.task.type',
                                       required=True, ondelete='restrict', index=True, copy=False)
    task_id = fields.Many2one(string='Task',
                              comodel_name='project.task',
                              required=False, ondelete='restrict', index=True, copy=False)
    analytic_account_id = fields.Many2one(related='contract_id.project_id.analytic_account_id',
                                          store=True, readonly=True)
    currency_id = fields.Many2one(related='contract_id.partner_id.property_purchase_currency_id',
                                  store=True, readonly=True)
    contract_type = fields.Selection(string='Contract Type',
                                     selection=[('cost_plus', 'Fixed amount/ Direct'),
                                                ('meter', 'Meter-based'),
                                                ('unit', 'Unit-based'),
                                                ('ratio', 'Ratio-based')],
                                    readonly=True, related="contract_id.contract_type")

    state = fields.Selection(string='Status',
                                selection=[('draft', 'Draft'),
                                           ('progress', 'In Progress'),
                                           ('done', 'Done'),
                                           ('cancel', 'Cancelled')],
                                required=True, default='draft',
                                copy=False, tracking=True)
    # Future Release: manage lines states separately from contract states
    contract_state = fields.Selection(related='contract_id.state', store=True, readonly=True)

    product_id = fields.Many2one(string='Product',
                                 comodel_name='product.product',
                                 required=True)

    quantity = fields.Float(string='Quantity',
                            required=True, default=1.0)
    quantity_purchased = fields.Float(string='Quantity Purchased',
                                      compute='_compute_qty_purchased', store=True, readonly=True)
    # po_line_ids = fields.One2many(string='PO Lines',
    #                               comodel_name='purchase.order.line',
    #                               inverse_name='contract_line_id',
    #                               readonly=True, copy=False)

    # @api.depends('po_line_ids', 'po_line_ids.product_qty', 'po_line_ids.state')
    # def _compute_qty_purchased(self):
    #     for line in self:
    #         line.quantity_purchased = sum(line.po_line_ids.filtered(
    #             lambda l: l.state in ['purchase', 'done',]).mapped('product_qty'))

    # def create_po_line(self):
    #     """
    #     Create purchase orders for lines.
    #     Will create a new PO unless an existing draft and related PO is found.
    #     :return: purchase.order.line created whether appended to existing POs or created new POs
    #     :rtype: recordset: purchase.order.line
    #     """
    #     self.ensure_one()
    #     # po_line = self.env['purchase.order.line']
    #     if self.contract_state != 'progress':
    #             raise UserError(_('You can generate purchases for in-progress contracts only.'))

    #     order = self.env['purchase.order']
    #     # Find existing POs, same contract is enough, since it is linked to only one project
    #     orders = self.env['purchase.order'].search([('contract_id', '=', self.contract_id.id),
    #                                                 ('company_id', '=', self.company_id.id),
    #                                                 ('state', 'in', ['draft', 'sent'])])

    #     if orders:
    #         order = orders[0]
    #     else:
    #         order = order.create({
    #             'origin': self.contract_id.name,
    #             'partner_id': self.contract_id.partner_id.id,
    #             'contract_id': self.contract_id.id,
    #             'project_id': self.contract_id.project_id.id,
    #             'currency_id': self.contract_id.currency_id.id,
    #             'date_order': fields.Datetime.now(),
    #             'company_id': self.company_id.id,
    #             Implement when stock is added on the project itself
    #             'picking_type_id': self.env['stock.picking.type'].search([('code', '=', 'incoming')], limit=1).id,
    #         })

        # Check vendor pricelist? The contract should override any pricelists, right?
        # po_line = self.env['purchase.order.line'].create({
        #     'order_id': order and order.id or False,  # This will raise an error if no order is found
        #     'contract_id': self.contract_id.id,
        #     # 'contract_line_id': self.id,
        #     'task_id': self.task_id.id,
        #     'project_id': self.contract_id.project_id.id,
        #     'product_id': self.product_id.id,
        #     'name': self.name,
        #     'product_qty': self.quantity - self.quantity_purchased,
        #     'product_uom': self.uom_id.id,
        #     'price_unit': self.price_unit,
        #     # 'tax_ids': [(6, 0, self.tax_ids.ids)], # Implement when taxes are confirmed to be used in contracts.
        # })

        # return po_line

    uom_id = fields.Many2one(string='Unit of Measure',
                             comodel_name='uom.uom',
                             required=True)
    uom_category_id = fields.Many2one(related='uom_id.category_id', store=True, readonly=True)

    price_unit = fields.Monetary(string='Unit Price', digits='Product Price',
                                 required=True, tracking=True, default=0.0)

    # Discount field is not implemented in purchases v14. Implement when upgraded to next versions of Odoo.
    # discount = fields.Float(string='Discount (%)', digits='Discount', default=0.0)
    tax_ids = fields.Many2many(string='Taxes',
                               comodel_name='account.tax', context={'active_test': False})
    price_tax = fields.Monetary(string='Tax Amount',
                                compute='_compute_line_amounts', store=True, readonly=True, tracking=True,
                                help='Taxes amount included in \'Total Price\' field')
    price_total = fields.Monetary(string='Total',
                                  compute='_compute_line_amounts', readonly=True, store=True, tracking=True,
                                  help='Total price including taxes.')
    price_subtotal = fields.Monetary(string='Subtotal',
                                     readonly=True, compute='_compute_line_amounts', store=True, tracking=True,
                                     help='Subtotal price excluding taxes.')

    def _compute_line_amounts(self):
        """
        Method to compute line amounts based on quantity and unit price
        Future releases should implement taxes and discounts
        """
        for line in self:
            taxes = line.tax_ids.compute_all(line.price_unit, line.contract_id.currency_id, line.quantity,
                                            product=line.product_id, partner=line.contract_id.partner_id)
            line.update({
                'price_tax': sum(t.get('amount', 0.0) for t in taxes.get('taxes', [])),
                'price_total': taxes['total_included'],
                'price_subtotal': taxes['total_excluded'],
            })

    company_id = fields.Many2one(related='contract_id.company_id', store=True, readonly=True)


class ProjectContractStage(models.Model):
    _name = 'project.contract.stage'
    _description = 'Project Contract Stage'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin']
    _order = 'sequence, id'
    _check_company_auto = True

    name = fields.Char(string='Stage', required=True, translate=True)
    sequence = fields.Integer(string='Sequence', required=True, default=1,
                              readonly=True, states={'draft': [('readonly', False)]})
    active = fields.Boolean(default=True)
    contract_id = fields.Many2one(string='Contract',
                                  comodel_name='project.contract',
                                  required=True,
                                  ondelete='cascade', index=True, copy=False, tracking=True)
    partner_id = fields.Many2one(related='contract_id.partner_id', store=True, readonly=True)
    date_start = fields.Date(string='Start Date',
                             readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    date_end = fields.Date(string='End Date',
                           readonly=True, states={'draft': [('readonly', False)]}, tracking=True)
    date_close = fields.Datetime(string='Date Closed', readonly=True, copy=False)
    percent = fields.Float(string='Percent', tracking=True)
    percent_amount = fields.Float(string="Percentage Result", compute='_compute_result', tracking=True)
    progress = fields.Float(string='Progress', store=True)
                            # compute the progress based on purchased/delivered quantities
                            # compute='_compute_progress',
    actual_progress = fields.Float(string='Actual progress', 
                                    default=0.0,
                                    store=True, tracking=True)
    stage_amount = fields.Float(string="Amount", default=0.0, store=True, tracking=True)
    unit = fields.Float(string="Number of Units/ Meters", tracking=True)
    unit_amount = fields.Float(string="Units/ Meters Result", compute='_compute_result', tracking=True)
    actual_unit = fields.Float(string="Actual Number of Units/ Meters", tracking=True)
    contract_type = fields.Selection(string='Contract Type',
                                    readonly=True, 
                                    related="contract_id.contract_type")
    state = fields.Selection(string='Status',
                             selection=[('draft', 'Draft'),
                                        ('waiting', 'Waiting Approval'),
                                        ('progress', 'In Progress'),
                                        ('done', 'Closed'),
                                        ('cancel', 'Cancelled')],
                             required=True, default='draft',
                             copy=False, tracking=True)

    @api.onchange('percent', 'contract_id.remain_amount', 'contract_id.discount', 'contract_id.discount_subtotal', 'contract_id.total')
    def _compute_result(self):
        """ Compute method to calculate the percentage/ unit amount.

        """
        for stage in self:
            stage.percent_amount = 0
            stage.unit_amount = 0
            if stage.percent and stage.contract_id.remain_amount:
                if stage.contract_id.discount:
                    stage.percent_amount = (stage.percent ) * stage.contract_id.discount_subtotal
                else:
                    stage.percent_amount = (stage.percent ) * stage.contract_id.remain_amount

            if stage.unit and stage.contract_id.price:
                result = 0
                if stage.contract_id.discount:
                    result = stage.contract_id.discount_subtotal / stage.contract_id.total
                    stage.unit_amount = stage.unit * result
                else:
                    result = stage.contract_id.price / stage.contract_id.total
                    stage.unit_amount = stage.unit * result



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

    def set_confirmed(self):
        for stage in self:
            stage.write({'state': 'waiting'})

    def set_waiting(self):
        for stage in self:
            stage.write({'state': 'progress'})

    def set_done(self):
        for stage in self:
            # if not stage.receipt_id:
            #     raise UserError(_('You must set a stage receipt before closing it.'))

            stage.write({
                'date_close': fields.Datetime.now(),
                'state': 'done'
            })

    def set_cancel(self):
        for stage in self:
            if stage.state != 'draft':
                raise UserError(_('You cannot cancel a stage which is not draft.'))

            stage.write({'state': 'cancel'})

    # Cash Requests are not linked to payments! This must be changed ASAP.
    payment_id = fields.Many2one(string='Payment',
                                 comodel_name='cash.order',
                                 copy=False, ondelete='restrict',
                                 readonly=False, states={'done': [('readonly', True)],
                                                         'cancel': [('readonly', True)]})
    settlement_id = fields.Many2one(string='Settlement',
                                    comodel_name='project.contract.settlement',
                                    copy=False, ondelete='restrict',
                                    readonly=False, states={'done': [('readonly', True)],
                                                            'cancel': [('readonly', True)]})
    receipt_id = fields.Many2one(string='Receipt',
                                 comodel_name='project.contract.receipt',
                                 copy=False, ondelete='restrict',
                                 readonly=False, states={'done': [('readonly', True)],
                                                         'cancel': [('readonly', True)]})
    user_id = fields.Many2one(string='Stage Responsible',
                              comodel_name='res.users',
                              required=True, default=lambda self: self.env.user,
                              tracking=True, index=True)
    company_id = fields.Many2one(related='contract_id.company_id', store=True, readonly=True)

    def write(self, vals):
        # TODO: @MRawi: Double check this
        # TODO: Consider contract itself is being cancelled.
        result = super().write(vals)
        # Make sure stages are not modified after initial confirmation
        # for stage in self:
        #     if stage.contract_id.state not in ['draft', 'pm_approval']:
        #         raise UserError(_('You cannot modify stages of a contract which is not approved by company owners.'))
        return result


class ProjectContractClause(models.Model):
    _name = 'project.contract.clause'
    _description = 'Project Contract Legal Clauses'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _order = 'sequence, id'
    _check_company_auto = True

    sequence = fields.Integer(string='Sequence', required=True, default=1)
    active = fields.Boolean(default=True)

    name = fields.Char(string='Title', required=True, translate=True)
    content = fields.Html(string='Content', required=True, translate=True)
    contract_id = fields.Many2one(string='Contract',
                                  comodel_name='project.contract',
                                  required=True, ondelete='cascade')
    company_id = fields.Many2one(related='contract_id.company_id', store=True, readonly=True)


class ProjectContractTemplate(models.Model):
    _name = 'project.contract.template'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Project Contract Template'
    _order = 'sequence, id'
    _check_company_auto = True

    sequence = fields.Integer(string='Sequence', required=True, default=1)
    active = fields.Boolean(default=True)

    name = fields.Char(string='Title', required=True, translate=True)
    clause_ids = fields.One2many(string='Clauses',
                                 comodel_name='project.contract.template.line',
                                 inverse_name='template_id',
                                 required=True, translate=True)
    company_id = fields.Many2one(string='Company',
                                 comodel_name='res.company',
                                 required=True, default=lambda self: self.env.company)


class ProjectContractTemplateLine(models.Model):
    _name = 'project.contract.template.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Project Contract Template Clauses'
    _order = 'sequence, id'
    _check_company_auto = True

    sequence = fields.Integer(string='Sequence', required=True, default=1)
    active = fields.Boolean(default=True)

    name = fields.Char(string='Title', required=True, translate=True)
    content = fields.Html(string='Content', required=True, translate=True)
    template_id = fields.Many2one(string='Template',
                                    comodel_name='project.contract.template',
                                    required=True, ondelete='cascade')

    company_id = fields.Many2one(related='template_id.company_id', store=True, readonly=True)


class ProjectConstructionCancel(models.Model):
    _name = 'project.construction.cancel.reason'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Project Construction Cancel Reason'
    _check_company_auto = True

    name = fields.Char(string='Reason', required=True, translate=True)
    description = fields.Text(string='Description')
    active = fields.Boolean(default=True)
    contract_ids = fields.One2many(string='Contracts',
                                   comodel_name='project.contract',
                                   inverse_name='cancel_reason_id')
    company_id = fields.Many2one(string='Company',
                                 comodel_name='res.company',
                                 default=lambda self: self.env.company)

class PaymentHistory(models.Model):

    _name = 'payment.history.line'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']
    _description = 'Payments History'
    _rec_name='history_line_id'

    history_line_id = fields.Many2one('project.contract')
    name = fields.Char(string="Name", tracking=True)
    date = fields.Date(string=' Date ', tracking=True)
    contract_stage_id = fields.Many2one(string='Contract Stage', tracking=True,
                                        comodel_name='project.contract.stage')
    percent = fields.Float(string='Payment Percent', tracking=True,
                            comodel_name='project.contract.stage')
    percent_amount = fields.Float(string="Percentage Result", comodel_name='project.contract.stage', tracking=True)
    progress = fields.Float(string='Progress', tracking=True,
                            comodel_name='project.contract.stage')
    actual_progress = fields.Float(string='Actual progress', tracking=True,
                                comodel_name='project.contract.stage')
    unit = fields.Float(string='Num of Units/ Meters', tracking=True,
                            comodel_name='project.contract.stage')
    unit_amount = fields.Float(string="Units/ Meters Result", comodel_name='project.contract.stage', tracking=True)
    actual_unit = fields.Float(string='Actual Num of Units/ Meters', tracking=True,
                                comodel_name='project.contract.stage')
    stage_amount = fields.Float(string="Stage amount", tracking=True,
                                comodel_name='project.contract.stage')
    payment_amount = fields.Float(string="Payment amount", tracking=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency")
    contract_type = fields.Selection(string='Contract Type',
                                    selection=[('cost_plus', 'Fixed amount/ Direct'),
                                                ('meter', 'Meter-based'),
                                                ('unit', 'Unit-based'),
                                                ('ratio', 'Ratio-based')],
                                    tracking=True)
    state = fields.Selection(string='Status',
                            selection=[('draft', 'Draft'),
                                        ('waiting', 'Waiting Approval'),
                                        ('progress', 'In Progress'),
                                        ('done', 'Closed'),
                                        ('cancel', 'Cancelled')],
                            tracking=True)