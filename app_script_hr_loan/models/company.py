
from odoo import api, models, fields

class res_company(models.Model):
    
    _inherit = 'res.company'

    max_employee =fields.Float(string="Max Percentage for Total Loans Per Employee" )
    max_department =fields.Float(string="Max Percentage for Total Loans Per Department" )
    allowed_number =fields.Integer(string="Allowed Number",help='Number of loans per employee , if its 0 thats mean no limit for number of loans',default=0)
    salary_rule_id = fields.Many2one('hr.salary.rule','Salary')
