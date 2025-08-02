# -*- coding: utf-8 -*-
# See LICENSE file for full copyright and licensing details.
import time
from datetime import datetime, date, timedelta
from odoo import models, fields, _, api
from odoo.tools import misc, DEFAULT_SERVER_DATE_FORMAT
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.tools.float_utils import float_compare
from odoo.exceptions import Warning, ValidationError


class job_line(models.Model):
    _name = 'job.line'
    _description = 'Job Line'

    name = fields.Char(string="Description", required=True)
    product_id = fields.Many2one(
        string="Product",
        comodel_name="product.product",
        required=True
    )
    price_unit = fields.Float(string="Cost",required=True )
    maintenance_id = fields.Many2one(
        string="Maintenance",
        comodel_name="maintenance.request",
    )
    installation_id = fields.Many2one(
        string="Installation Request",
        comodel_name="equipment.installation",
    )

