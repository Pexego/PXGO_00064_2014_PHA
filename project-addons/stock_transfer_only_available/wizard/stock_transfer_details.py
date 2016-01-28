# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
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
from openerp import models, fields, api, exceptions, _
from openerp.tools.float_utils import float_compare


class StockTransferDetails(models.Model):

    _inherit = 'stock.transfer_details'

    @api.one
    def do_detailed_transfer(self):
        stock_loc_id = self.picking_id.picking_type_id.warehouse_id.lot_stock_id.id
        for line in self.item_ids:
            if line.sourceloc_id.id not in self.env['stock.location'].search(
                    [('id', 'child_of', stock_loc_id)])._ids:
                continue
            quant_vals = [('product_id', '=', line.product_id.id),
                          ('lot_id', '=', line.lot_id and line.lot_id.id or
                           False),
                          ('location_id', '=', line.sourceloc_id.id),
                          '|', ('reservation_id.picking_id', '=',
                                self.picking_id.id),
                          ('reservation_id', '=', False)]
            quants = self.env['stock.quant'].search(quant_vals)
            total_qty = sum([x['qty'] for x in quants.read(['qty'])])
            total_qty_uom = self.env['product.uom']._compute_qty(
                line.product_id.uom_id.id, total_qty,
                line.product_uom_id.id)
            difference = float_compare(
                total_qty_uom, line.quantity,
                precision_rounding=line.product_uom_id.rounding)
            if difference < 0:
                raise exceptions.Warning(
                    _('Quantity error'),
                    _('Not found enought stock in %s for product %s') %
                    (line.sourceloc_id.name, line.product_id.name))
        return super(StockTransferDetails, self).do_detailed_transfer()
