# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus I+D+i All Rights Reserved
#    $Iván Alvarez <informatica@pharmadus.com>$
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class StockAvailable(models.TransientModel):
    _name = 'stock.available'
    _description = 'Available stock for bill of materials'
    _rec_name = 'product_id'

    product_id = fields.Many2one(string='Product',
                                 comodel_name='product.template')
    bom_id = fields.Many2one(string='Bills of materials',
                             comodel_name='mrp.bom',
                             domain="[('product_tmpl_id', '=', product_id)]")
    product_qty = fields.Integer(string='Quantity to calculate')

    @api.onchange('product_id')
    def update_bom(self):
        bom_ids = self.env['mrp.bom'].search([('product_tmpl_id', '=', self.product_id.id)])
        self.bom_id = bom_ids[0] if bom_ids else False


class StockAvailableDetails(models.TransientModel):
    _name = 'stock.available.details'
    _description = 'Available stock for bill of materials lines'
    _rec_name = 'product'

    product = fields.Char(string='Product')
    qty_required = fields.Float(string='Quantity required', digits=dp.get_precision('Product Unit of Measure'))
    qty_available = fields.Float(string='Quantity On Hand', digits=dp.get_precision('Product Unit of Measure'))
    uom = fields.Char(string='Unit of measure')
    bom_stock = fields.Many2one(comodel_name='stock.available', readonly=True)


class StockAvailable(models.TransientModel):
    _inherit = 'stock.available'

    bom_lines = fields.One2many(string='Bill of materials details', comodel_name='stock.available.details',
                                inverse_name='bom_stock')

    @api.one
    def action_compute(self):
        self.bom_lines.unlink()
        for line in self.bom_id.bom_line_ids:
            self.bom_lines.create({
                'product': line.product_id.name_template,
                'qty_required': line.product_qty * self.product_qty,
                'qty_available': line.product_id.qty_available,
                'uom': line.product_uom.name,
                'bom_stock': self.id
            })
        return self
