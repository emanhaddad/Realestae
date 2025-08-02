# -*- encoding: utf-8 -*-
# © 2017 Mackilem Van der Laan, Trustcode
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models , _ 


class hr_overtime(models.Model):
    _name = 'hr.overtime'
    _description = 'Employees Overtime'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name" , default=lambda self: _('New'))
    date = fields.Date(string="Date", default=fields.Date.today() , readonly=True)
    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
    )
    hours = fields.Float(string="Hours", required=True ,tracking=3)
    working_date = fields.Date(string="Working Date",required=True ,tracking=3)
    notes = fields.Text(string="Description", tracking=3)
    state = fields.Selection(
        string="State",
        selection=[
            ('draft', 'new'),
            ('department', 'Waiting Department Manager'),
            ('hr', 'Waiting HR Manager'),
            ('done', 'Done'),
            ('cancel','Canceled'),
        ],default='draft' , tracking=3
    )
    active = fields.Boolean(string="Active", default=True)
    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        default=lambda self: self.env.user
    )
    department_id = fields.Many2one(
        string="Department",
        comodel_name="hr.department",
        related="employee_id.department_id",
        readonly=True,
    )
    manager_id = fields.Many2one(
        string="Department Manager",
        comodel_name="hr.employee",
        related="department_id.manager_id",
        readonly=True,
    )
    company_id = fields.Many2one('res.company', string='Company',
        default=lambda self: self.env.company)

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['working_date']))
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.overtime', sequence_date=seq_date) or _('New')

        result = super(hr_overtime, self).create(vals)
        return result
    
    def department(self):
        self.state = 'department'
    
    def hr(self):
        self.state = 'hr'
    
    def cancel(self):
        self.state = 'cancel'
    
    def set_to_draft(self):
        self.state = 'draft'