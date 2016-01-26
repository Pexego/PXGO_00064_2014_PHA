# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, fields, api


class StockPickingType(models.Model):
    _inherit = 'stock.picking.type'

    product_drop_default = fields.Boolean('Default picking type for product drop?',
                                          default=False)

    @api.one
    def check_only_one_product_drop(self):
        # Only one can be active in each warehouse
        picking_types = self.search([
            ('warehouse_id', '=', self.warehouse_id.id),
            ('code', '=', 'internal'),
            ('product_drop_default', '=', True),
            ('id', '<>', self.id)
        ])
        for pt in picking_types:
            pt.product_drop_default = False

    @api.model
    def create(self, vals):
        res = super(StockPickingType, self).create(vals)

        if res and res.product_drop_default:
            res.check_only_one_product_drop()

        return res

    @api.multi
    def write(self, vals):
        res = super(StockPickingType, self).write(vals)

        if vals.get('product_drop_default', False):
            for pt in self:
                pt.check_only_one_product_drop()

        return res