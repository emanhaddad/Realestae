# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AccountAnalyticContract(models.Model):
    _name = 'realestate.rent.contract'
    _inherit = ['mail.thread', 'mail.activity.mixin']


    name = fields.Char('Name')
    code = fields.Char('Code')
    active = fields.Boolean(
        string='Active', default=True,
        help="If unchecked, it will allow you to hide the product without removing it.")
    recurring_rule_type = fields.Selection(
        [
         ('monthly', 'Month(s)'),
         ('yearly', 'Year(s)'),
         ],
       
        help="Specify Interval for payment generation.",
    )
    recurring_interval = fields.Integer(
     
    
        help="Repeat every (Month/Year)",
    )

    term_ids = fields.One2many('hr.contract.term', 'rent_contract_id', string="Terms")


class ContractTypeTerms(models.Model):

    _name = "hr.contract.term"
    _description = 'Contract Terms'
    _order = 'term_no'

    name = fields.Char(string='Term' ,required=True)
    term_no = fields.Integer("Term Number", required=True)
    description = fields.Text('Description')
    type = fields.Selection([
        ('mandatory', 'Mandatory'),
        ('optional', 'Optional')], string='Type', default='mandatory', required=True)
    rent_contract_id = fields.Many2one("realestate.rent.contract")
