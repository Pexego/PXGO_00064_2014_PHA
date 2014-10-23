# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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

from openerp import models, fields, api, exceptions, _


class product_product(models.Model):

    _inherit = 'product.product'

    protocol_ids = fields.Many2many('product.protocol', 'product_protocol_rel',
                                    'product_id', 'protocol_id', 'Protocols')
    protocol_count = fields.Integer('Protocols count', compute='_get_protocol_count')

    @api.one
    @api.depends('protocol_ids')
    def _get_protocol_count(self):
        self.protocol_count = len(self.protocol_ids)

class ProductTemplate(models.Model):

    _inherit = "product.template"

    protocol_count = fields.Integer('Protocols count', compute='_get_protocol_count')

    @api.one
    @api.depends('product_variant_ids.protocol_ids')
    def _get_protocol_count(self):
        self.protocol_count = sum([p.protocol_count for p in self.product_variant_ids])

    def action_view_protocols(self, cr, uid, ids, context=None):
        products = self._get_products(cr, uid, ids, context=context)
        result = self._get_act_window_dict(cr, uid, 'quality_protocol_report.action_view_product_protocol', context=context)
        if len(ids) == 1 and len(products) == 1:
            result['context'] = "{'default_product_ids': [" + str(products[0]) + "], 'search_default_product_ids': " + str(products[0]) + "}"
        else:
            result['domain'] = "[('product_ids','in',[" + ','.join(map(str, products)) + "])]"
            result['context'] = "{}"
        return result


class product_protocol(models.Model):

    _name = 'product.protocol'

    name = fields.Many2one('protocol.type', 'Type', readonly=True, related='protocol_id.type_id')
    product_ids = fields.Many2many('product.product', 'product_protocol_rel',
                                  'protocol_id', 'product_id', 'Products')
    protocol_id = fields.Many2one('quality.protocol.report', 'Protocol', required=True)

    @api.one
    @api.constrains('name', 'product_ids')
    def unique_name_product(self):
        for product in self.product_ids:
            if self.name.id in [x.name.id for x in product.protocol_ids if x.id != self.id]:
                raise exceptions.ValidationError(_("The product %s has another protocol with the same type") % product.name)
