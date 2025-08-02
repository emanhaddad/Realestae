
from dateutil.relativedelta import relativedelta
from odoo import api, fields, models, _
from odoo.exceptions import UserError,ValidationError


class RealEstateMaintenance(models.Model):

    _name = 'real.estate.maintenance'
    _description = 'real Estate Maintenance'
    _inherit = 'maintenance.request'

    sequence = fields.Char(string="Sequence" , default=lambda self: _('New'))
    real_estate_id = fields.Many2one(
        'real.estate',
        'Real Estate',
        help='Real Estate',
        required=True, tracking=True)
    type = fields.Selection([('all_property','All property'),('specific_units','Specific Units')],default='all_property',string="Maintenance Type")
    unit_id = fields.Many2one('real.estate.units', string="Unit",)
    amount= fields.Float(string="Amount")
    expense_request_id =  fields.Many2one(
        'expense.request',
        string='Expense',
    )
    state = fields.Selection([('draft', 'Draft'),('waiting_evaluation', 'Waiting evaluation'),('in_progress', 'In Progress'),
                              ('received','Receiving'),
                              ('done', 'Done'),('blocked','Blocked')],
                             'State', readonly=True,default='draft', tracking=True)

    image_ids = fields.Many2many(
        string="Images",
        comodel_name="ir.attachment",
        relation="realestate_maintenace_attachments",
        column1="mainteance_id",
        column2="attachment_id",
    )
    issue = fields.Html(string="Issue", )
    maintenance_team_id = fields.Many2one(
        string="Maintenace",
        comodel_name="maintenance.team",
        required=False,
    )
    component_ids = fields.Many2many('product.product', string='Required spares')
    requisition_lines = fields.One2many('requisition.line', 'request_id')
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    count_payment = fields.Integer(compute='_compute_je', string="Payment")
    move_id = fields.Many2one('account.move',string='Request Ref',readonly=True)
    journal_id = fields.Many2one('account.journal',string='Journal',domain="[('type','in',['cash','bank'])]")

    @api.model
    def create(self, vals):
        if vals.get('sequence', _('New')) == _('New'):
            vals['sequence'] = self.env['ir.sequence'].next_by_code('real.estate.maintenance') or _('New')

        result = super(RealEstateMaintenance, self).create(vals)
        return result

    @api.constrains('amount','duration')
    def _check_amount(self):
        for rec in self:
            
            if rec.amount <0:
                raise UserError(_("Please set expected amount"))
            if rec.duration <0:
                raise UserError(_("Please set expected duration"))
            if not rec.real_estate_id.warranty_start_date:
                raise UserError(_("Please set Warranty start date on the property"))
            if rec.real_estate_id.warranty_end_date and rec.create_date.date() > rec.real_estate_id.warranty_end_date:
                raise UserError(_("Warranty has expired for this unit"))

    def action_inprogress(self):
        self.create_expense_requset()
        if not self.exchange_type_id:
            raise UserError("Please select the exchange type")
        if not self.real_estate_id.expenss_account_id.id:
            raise UserError("Please enter the expense account of the real estate")
        
        payment_id = self.env['cash.order'].create({
                    # 'state': 'general',
                    # 'name': new_cash_order_name,
                    'date': self.request_date,
                    'exchange_type_id' : self.exchange_type_id.id,
                    'partner_id': self.user_id.id,
                    'amount' : self.amount,
                    'journal_id' : self.journal_id.id,
                    'disc' : self.name + ' ' + 'طلب صيانة',
                    'maintenance_request_ids' : self.id,
                    'order_line_ids': [(0, 0, {
                        'description': 'أمر صرف لصيانة',
                        'account_id': self.real_estate_id.expenss_account_id.id,
                        'amount': self.amount,
                        # 'state': 'general',
                    })],
                })

        payment_id.action_confirm()
        payment_id.action_finance()
        self.move_id = payment_id.move_id.id
        self.write({'state': 'in_progress'})

    def revise_request(self):
        self.write({'state': 'received'})

    def action_done(self):
        self.write({'state': 'done'})

    def action_evaluation(self):
        self.write({'state': 'waiting_evaluation'})

    def _compute_je(self):
        if self.move_id:
            self.count_payment = 1
        else:
            self.count_payment = 0

    def action_payment(self):
    
        tree_view = self.env.ref('cash_request.cash_order_tree_view')
        form_view = self.env.ref('cash_request.cash_order_view')
        return {
            'type': 'ir.actions.act_window',
            'name': 'Payment Vouchers',
            'res_model': 'cash.order',
            'view_type': 'form',
            'view_mode': 'tree,form',
            'views': [(tree_view.id, 'tree'), (form_view.id, 'form')],
            'domain': [('maintenance_request_ids', '=', self.id)],

        }

    def create_expense_requset(self):

        vals = {
            'property_id': self.real_estate_id.id,
            'amount': self.amount,
            'state':'approve',
            'unit_id':self.unit_id.id,
            'description':"Maintenance Of"+self.real_estate_id.name+""
            }
        expense = self.env['expense.request'].create(vals)
        
        self.write({
            'expense_request_id' : expense,
        })

    @api.onchange('property_id')
    def _first_field_onchange(self):
        res = {}

        res['domain']={'unit_id':[('base_property_id', '=', self.property_id.id)]}
        return res

    '''
    def set_to_draft(self):
        self.write({'state':'draft'})


    def approve(self):
        self.create_expense_requset()

        return self.write({'state': 'approve'})


    def confirm(self):
        return self.write({'state': 'confirm'})

    
    '''