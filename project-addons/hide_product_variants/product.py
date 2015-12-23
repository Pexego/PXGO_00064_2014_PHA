# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, tools


class ProductProduct(models.Model):

    _inherit = 'product.product'

    @api.one
    def _set_image_variant_image(self):
        image = tools.image_resize_image_big(self.image)
        self.product_tmpl_id.image = image
        self.image_variant = image

    @api.one
    def _set_image_variant_image_small(self):
        image = tools.image_resize_image_big(self.image_small)
        self.product_tmpl_id.image = image
        self.image_variant = image

    @api.one
    def _set_image_variant_image_medium(self):
        image = tools.image_resize_image_big(self.image_medium)
        self.product_tmpl_id.image = image
        self.image_variant = image

    image = fields.Binary(inverse='_set_image_variant_image')
    image_medium = fields.Binary(inverse='_set_image_variant_image_medium')
    image_small = fields.Binary(inverse='_set_image_variant_image_small')
