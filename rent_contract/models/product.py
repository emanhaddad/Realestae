# -*- encoding: utf-8 -*-
#########################################################################

from odoo import api, fields, models, _
import base64, urllib
from io import BytesIO
import requests, base64, sys
import os
import odoo.netsvc

class product_product(models.Model):
    _inherit = "product.product"


    @api.model
    def copy(self, default=None):
        if not default:
            default = {}
        default.update({
            'default_code': False,
            'images_ids': False,
        })
        return super(product_product, self).copy(default)

    def get_main_image(self):
        images_ids = self.read(['image_ids'])['image_ids']
        if images_ids:
            return images_ids[0]
        return False
    
    def _get_main_image(self):
        res = {}
        img_obj = self.env['product.images']
        for id in self:
            image_id = self.get_main_image()
            if image_id:
                image = img_obj.browse(image_id)
                res[id] = image.file
            else:
                res[id] = False
        return res

    
    image_ids = fields.One2many(
            'product.images',
            'product_id',
            'Product Images'
    )
    default_code = fields.Char('Reference', size=64, require='True')
    product_image = fields.Char(compute='_get_main_image', type="binary", method=True)
    
   


class product_images(models.Model):

    "Products Image gallery"
    _name = "product.images"
    _description = __doc__
    

    name = fields.Char('Image Title', size=100, required=True)
    file_db_store = fields.Binary('Image stored in database')
    comments = fields.Text('Comments')
    product_id = fields.Many2one('product.product', 'Product')
    product_t_id = fields.Many2one('product.template', 'Product Images')

    _sql_constraints = [('uniq_name_product_id', 'UNIQUE(product_id, name)',
                _('A product can have only one image with the same name'))]






