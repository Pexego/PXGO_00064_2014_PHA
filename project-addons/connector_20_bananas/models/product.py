# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class ProductProduct(models.Model):

    _inherit = 'product.product'

    bananas_synchronized = fields.Boolean('Synchronized with 20 bananas')
    external_image_url = fields.Char(compute='_compute_external_imagen_url')

    @api.depends('default_code')
    def _compute_external_imagen_url(self):
        for product in self:
            url_template = self.env['ir.config_parameter'].get_param(
                'bananas.img.url')
            if url_template:
                product.external_image_url = url_template % product.default_code
