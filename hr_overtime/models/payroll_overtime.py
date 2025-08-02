# -*- encoding: utf-8 -*-
# © 2017 Mackilem Van der Laan, Trustcode
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models , _ 


class hr_payroll_overtime(models.Model):
    _name = 'hr.payroll.overtime'
    _description = 'Employees Overtime payroll'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']

    name = fields.Char(string="Name" , default=lambda self: _('New'))
    date = fields.Date(string="Creation Date",default=fields.date.today(),readonly=True )
    start = fields.Date(string="Start Date", )
    end = fields.Date(string="End Date", )

    payroll_date = fields.Date(string="Payroll Date", )

    user_id = fields.Many2one(
        string="User",
        comodel_name="res.users",
        default=lambda self: self.env.user,
        readonly=True,
    )
    line_ids = fields.One2many(
        string="Overtime Lines",
        comodel_name="hr.payroll.overtime.line",
        inverse_name="overtime_id",
    )
    state = fields.Selection(
        string="State",
        selection=[
            ('draft', 'new'),
            ('hr', 'Waiting HR Manager'),
            ('gm', 'Waiting General Manager'),
            ('waiting', 'Waiting Payroll computation'),
            ('done', 'Done'),
            ('cancel','Canceled'),
        ],default='draft' , tracking=3
    )
    active = fields.Boolean(string="Active", default=True)
    department_ids = fields.Many2many(
        string="Departments",
        comodel_name="hr.department",
        relation="overtime_payroll_department_relation",
        column1="overtime_id",
        column2="department_id",
    )
    

    @api.model
    def create(self, vals):
        if vals.get('name', _('New')) == _('New'):
            seq_date = None
            if 'date' in vals:
                seq_date = fields.Datetime.context_timestamp(self, fields.Datetime.to_datetime(vals['start']))
            vals['name'] = self.env['ir.sequence'].next_by_code('hr.payroll.overtime', sequence_date=seq_date) or _('New')

        result = super(hr_payroll_overtime, self).create(vals)
        return result

    def waiting(self):
        #self.line_ids.state = 'waiting'
        self.state = 'waiting'

    def gm(self):
        #self.line_ids.write({'state','gm'})
        self.state = 'gm'
    
    def hr(self):
        #self.line_ids.write({'state','hr'})
        self.state = 'hr'
    
    def cancel(self):
        #self.line_ids.write({'state','cancel'})
        self.state = 'cancel'
    
    def set_to_draft(self):
        #self.line_ids.write({'state','draft'})
        self.state = 'draft'
    

    def get_overtime(self):
        self.line_ids.unlink()
        for department_id in self.department_ids:
            employee_ids = self.env['hr.employee'].search([('department_id','=',department_id.id)])
            for employee_id in employee_ids:
                overtime_ids = self.env['hr.overtime'].search([
                    ('employee_id','=',employee_id.id),
                    ('working_date','>', self.start),
                    ('working_date','<=', self.end),
                    ('state','=','hr'),
                ])
                hours = sum(overtime_id.hours for overtime_id in overtime_ids)
                if hours > 0 : 
                    self.env['hr.payroll.overtime.line'].create({
                        'employee_id':employee_id.id,
                        'hours': hours,
                        'overtime_id':self.id,
                    })
                    overtime_ids.write({'state':'done'})


class hr_payroll_overtime_line(models.Model):
    _name = 'hr.payroll.overtime.line'
    _description = 'Employees Overtime payroll Lines'
    _inherit = [ 'mail.thread', 'mail.activity.mixin']

    employee_id = fields.Many2one(
        string="Employee",
        comodel_name="hr.employee",
        required=True,
    )
    hours = fields.Float(string="Hours", required=True ,tracking=3)
    amount = fields.Float(string="Amount",tracking=3)
    department_id = fields.Many2one(
        string="Department",
        comodel_name="hr.department",
        related="employee_id.department_id",
        readonly=True,
    )
    state = fields.Selection(
        string="State",
        selection=[
            ('draft', 'new'),
            ('hr', 'Waiting HR Manager'),
            ('gm', 'Waiting General Manager'),
            ('waiting', 'Waiting Payroll computation'),
            ('done', 'Done'),
            ('cancel','Canceled'),
        ],default='draft' , tracking=3
    )
    overtime_id = fields.Many2one(
        string="Overtime",
        comodel_name="hr.payroll.overtime",
    )
    start = fields.Date(string="Start Date", realated="overtime_id.start")
    end = fields.Date(string="End Date", realated="overtime_id.end")

    payroll_date = fields.Date(string="Payroll Date", related="overtime_id.payroll_date")

    payslip_id = fields.Many2one(
        string="HR Payslip",
        comodel_name="hr.payslip",
        readonly=True
    )
