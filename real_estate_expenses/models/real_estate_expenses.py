from odoo import models, fields, api ,_
from datetime import datetime, timedelta
from odoo.exceptions import ValidationError, AccessError,UserError

class expense_request(models.Model):
    _name = "expense.request"
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name='property_id'

    code=fields.Char('Reference',index=True,readonly=True)
    date = fields.Date('Date',default=datetime.today(), tracking=True)
    property_id= fields.Many2one('real.estate', string="Property", tracking=True)
    unit_id= fields.Many2one('real.estate.units', string="Unit", tracking=True)
    supervisor = fields.Many2one(related="property_id.supervisor_id", string="Supervisor", tracking=True)
    expense_type = fields.Many2one('expense.type', string="Type", tracking=True)
    description=fields.Text('Description',index=True, tracking=True)
    currency_id = fields.Many2one('res.currency', help='The currency used to enter statement', string="Currency", oldname='currency')
    amount= fields.Monetary(string="Amount",required=True, tracking=True)
    exp_type_name = fields.Char(related="expense_type.name", string="Type Name", store=True, tracking=True) 
    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.user.company_id)
    state = fields.Selection([('draft', 'Draft'),
                              ('confirm', 'Confirmed'),
                              ('approve', 'Approved'),
                              ('transferd', 'Transferd'),],
                             'State', readonly=True,default='draft', tracking=True)
    company_id = fields.Many2one('res.company',readonly=True, string='Company', default=lambda self: self.env.user.company_id)
   
   
    attachment_number = fields.Integer(compute='_compute_attachment_number', string='Number of Attachments')

    payment_method = fields.Many2one(
        string="Payment Method/ Journal",
        comodel_name="account.journal",
        domain="[('type', 'in', ('cash','bank'))]",
        tracking=True
    )
    exchange_type_id = fields.Many2one('exchange.type', 'Exchange Type', tracking=True)
    count_payment = fields.Integer(compute='_compute_je', string="Payment", tracking=True)
    move_id = fields.Many2one('account.move', string='Move',required=False,readonly=True, tracking=True)
    
 

    def unlink(self):
        for record in self:
            if record.state not in ('draft'):
                raise UserError(_('Sorry! You cannot delete expense request not in Draft state.'))
        return models.Model.unlink(self)

    @api.model
    def default_get(self, fields):
        res = super(expense_request, self).default_get(fields)
        next_seq = self.env['ir.sequence'].get('expenses.request')
        res.update({'code': next_seq})
        return res
    
    @api.onchange('property_id')
    def _first_field_onchange(self):
        res = {}

        res['domain']={'unit_id':[('base_property_id', '=', self.property_id.id)]}
        return res

    
    def set_to_draft(self):
        self.write({'state':'draft'})


    def approve(self):
        return self.write({'state': 'approve'})

    def confirm(self):
        if self.amount<=0:
            raise ValidationError(_("Sorry !! Expense Amount must be Grater than zero"))
        return self.write({'state': 'confirm'})

    def transfer(self):
        if not self.exchange_type_id:
            raise UserError("Please select the exchange type")
        if not self.property_id.expenss_account_id.id:
            raise UserError("Please enter the expense account of the real estate")
        
        payment_id = self.env['cash.order'].create({
                    # 'state': 'general',
                    # 'name': new_cash_order_name,
                    'date': self.date,
                    'exchange_type_id' : self.exchange_type_id.id,
                    'partner_id': self.env.user.partner_id.id,
                    'amount' : self.amount,
                    'journal_id' : self.payment_method.id,
                    'disc' : self.code + ' ' + 'طلب مصروف',
                    'expense_request_ids' : self.id,
                    'order_line_ids': [(0, 0, {
                        'description': 'أمر صرف',
                        'account_id': self.property_id.expenss_account_id.id,
                        'amount': self.amount,
                        # 'state': 'general',
                    })],
                })

        payment_id.action_confirm()
        payment_id.action_finance()
        self.move_id = payment_id.move_id.id
        # self.create_move()
        return self.write({'state': 'transferd'})

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
            'domain': [('expense_request_ids', '=', self.id)],

        }

    def _compute_je(self):
        if self.move_id:
            self.count_payment = 1
        else:
            self.count_payment = 0
    
    def attachment_tree_view(self):
        domain = ['&', ('res_model', '=', 'expense.request'), ('res_id', 'in',self.ids)]
        res_id = self.ids and self.ids[0] or False     
        return {
          'name': _('Attachments'),           
          'domain': domain,          
          'res_model': 'ir.attachment', 
          'type': 'ir.actions.act_window',
          'view_id': False,
          'view_mode': 'kanban,tree,form',
          'view_type': 'form',
          'help': _('''<p class="oe_view_nocontent_create">
           
                                    Attach
    documents of your employee.</p>'''),
         'limit': 80,
         'context': "{'default_res_model': '%s','default_res_id': %d}"% (self._name, res_id)}
    
    def _compute_attachment_number(self):
        attachment_data = self.env['ir.attachment'].read_group([('res_model', '=', 'expense.request'), ('res_id', 'in', self.ids)], ['res_id'], ['res_id'])
        attachment = dict((data['res_id'], data['res_id_count']) for data in attachment_data)
        for expense in self:
            expense.attachment_number = attachment.get(expense.id, 0) 


class expense_type(models.Model):
    _name = "expense.type"
    
    name=fields.Char('Name',index=True)
    code=fields.Char('Code',index=True)
    is_active = fields.Selection([("yes","Yes"),("no","NO")],'Active')
    active = fields.Boolean(
        string='Active', default=True,
        help="If unchecked, it will allow you to hide the product without removing it.")