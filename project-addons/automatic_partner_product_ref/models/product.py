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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, SUPERUSER_ID
import base_conversion


class ProductProduct(models.Model):
    _inherit = 'product.product'

    default_code = fields.Char('Internal Reference', select=True, readonly=True)

    @api.one
    def _compute_reference(self):
        if self.default_code:
            reference = self.default_code
        else:
            reference = 'F' + base_conversion.baseN(self.id, 36,
                                         'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                                         4)
        return reference

    @api.model
    def create(self, vals):
        res = super(ProductProduct, self).create(vals)
        if not res.default_code:
            res.default_code = res._compute_reference()
        return res

    @api.multi
    def write(self, vals):
        if len(self.ids) == 1 and (not self.default_code) and\
                not vals.get('default_code', False):
            vals['default_code'] = self._compute_reference()
        return super(ProductProduct, self).write(vals)

    def init(self, cr):
        product_ids = self.search(cr, SUPERUSER_ID, [('default_code', 'in', (False, ''))])
        products = self.browse(cr, SUPERUSER_ID, product_ids)
        for p in products:
            p.default_code = p._compute_reference()