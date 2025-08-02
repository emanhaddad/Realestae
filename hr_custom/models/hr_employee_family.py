# -*- encoding: utf-8 -*-
# © 2017 Mackilem Van der Laan, Trustcode
# © 2017 Danimar Ribeiro, Trustcode
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl.html).

from odoo import api, fields, models


class hr_employee_family(models.Model):
    _name = 'hr.employee.family'
    _description = 'HR Dependant description'

    name = fields.Char(string='Name of Sponsor', store=True, required=True)
    image = fields.Binary(string = "Image")
    relation_identity = fields.Char(string="identity")
    relation = fields.Selection([('father', 'Father'),
        ('mother', 'Mother'),('daughter', 'Daughter'),
        ('son', 'Son'),('husband', 'husband'),
        ('wife', 'Wife'),('wife_without_maternity', 'Wife Without Maternity')], string='Relationship', required=True, help='Relation with employee')
    birthday = fields.Date('Date of Birth')
    employee_id = fields.Many2one('hr.employee', string="Employee",required=True , help='Select corresponding Employee')
    company_id = fields.Many2one(
        comodel_name='res.company',related="employee_id.company_id",
        default=lambda self: self.env.user.company_id ,store=True,
    )
    passport = fields.Char(string="Passport", )
    iqamaa = fields.Char(string="Iqamaa", )
    iqamaa_expiery = fields.Date(string="Iqamaa Expiry Date", )
    insurance_company = fields.Char(string="Insurance Company", )
    insurance_end = fields.Date(string="Insurance expiry", )

