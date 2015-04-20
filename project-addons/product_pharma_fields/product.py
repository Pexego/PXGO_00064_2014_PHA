# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
#    $Marta Vázquez Rodríguez <marta@pexego.es>$
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

from openerp import models, fields, api


class ProductLine(models.Model):

    _name = 'product.line'

    name = fields.Char('Name', size=64, required=True)

class ProductSubline(models.Model):

    _name = "product.subline"

    name = fields.Char('Name', size=64, required=True)

class ProductProduct(models.Model):

    _inherit = "product.product"

    cn_code = fields.Char('CN code', size=12)


class ProductTemplate(models.Model):

    _inherit = "product.template"

    cn_code = fields.Char('CN code', related="product_variant_ids.cn_code")
    objective = fields.Selection((('alimentation', 'Alimentation'),
                                  ('pharmacy', 'Pharmacy')), 'Objective')
    packing = fields.Char('Packing', size=12)
    country = fields.Many2one('res.country', 'Country')
    qty = fields.Float('Quantity')
    udm = fields.Many2one('product.uom', 'UdM')
    clothing = fields.Selection((('dressed', 'Dressed'),
                                 ('naked', 'Naked')), 'Clothing')
    customer = fields.Many2one('res.partner', 'Customer')
    line = fields.Many2one('product.line', 'Line')
    subline = fields.Many2one('product.subline', 'SubLine')

    @api.model
    def create(self, vals):
        tmpl = super(ProductTemplate, self).create(vals)
        if vals.get('cn_code'):
            tmpl.cn_code = vals['cn_code']

        return tmpl
