# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api , fields, models , _
from odoo.osv import expression

class hr_employee(models.Model):
    _inherit = 'hr.employee'

    name_english = fields.Char(string="Name (English)", )
    family_ids = fields.One2many(
        string="Family",
        comodel_name="hr.employee.family",
        inverse_name="employee_id",
    )
    job_identification = fields.Integer(string="Job Identification", )
    iqama = fields.Char(string="Iqama", )
    
    expiration_date_residence = fields.Date(string="Expiration Date Residence")
    passport_expiry_date = fields.Date(string="Passport Expiry Date")
    work_permit_expiration_date = fields.Date(string="Work Permit Expiration Date")
    job_join_date = fields.Date(string="Joining  Date")
    employee_type = fields.Selection([('full', 'Full Time'),
                                    ('part', 'Part Time'),
                                    ('contract','Contract'),
                                    ('other','Other')], 
                                    string="Employment Type", tracking=True)


    start_date = fields.Date(string="Start Date", )
    contract_end_date = fields.Date(string="Contract End Date", )

    first_contract_date = fields.Date(string="First Contract Date", readonly=False ,store=True, compute=False , groups="hr.group_hr_user")

    @api.depends('name_english', 'name')
    def name_get(self):
        result = []
        for line in self:
            name = line.name or ''
            if line.name_english:
                name += " (%s)" % line.name_english
            result.append((line.id, name))
        return result


    _sql_constraints = [
        ('job_identification_uniq', 'unique (job_identification)', "The Job  ID must be unique, this one is already assigned to another employee."),
        ('iqama_uniq', 'unique (iqama)', "The iqama must be unique, this one is already assigned to another employee.")
    ]
