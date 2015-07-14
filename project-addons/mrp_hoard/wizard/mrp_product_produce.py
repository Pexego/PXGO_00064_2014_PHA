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
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp


class MrpProductProduceReturnLine(models.TransientModel):
    _name = 'mrp.product.produce.return.line'

    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Quantity (in default UoM)',
                               digits_compute=dp.get_precision(
                                   'Product Unit of Measure'))
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    location_id = fields.Many2one('stock.location', 'Dest location')
    produce_id = fields.Many2one('mrp.product.produce')


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    _defaults = {
        'mode': lambda *x: 'consume',
    }

    return_lines = fields.One2many('mrp.product.produce.return.line',
                                   'produce_id', 'Products To return')

    def on_change_qty(self, cr, uid, ids, product_qty, consume_lines,
                      context=None):
        prod_obj = self.pool.get("mrp.production")
        uom_obj = self.pool.get("product.uom")
        production = prod_obj.browse(cr, uid, context['active_id'],
                                     context=context)
        new_consume_lines = []
        for move in production.move_lines:
            for line in move.return_operation_ids:
                new_consume_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.qty - line.hoard_returned_qty -
                    line.qty_scrapped,
                    'lot_id': line.lot_id
                }))

        return {'value': {'consume_lines': new_consume_lines}}

    @api.model
    def get_operations(self, move):
        stop = False
        move_aux = move
        while not stop:
            if move_aux.split_from:
                move_aux = move_aux.split_from
            else:
                stop = True
        return move_aux.return_operation_ids

    @api.multi
    def do_produce(self):
        res = super(MrpProductProduce, self.with_context(no_return_operations=True)).do_produce()
        originals = self.env['stock.move']
        production = self.env['mrp.production'].browse(self.env.context.get('active_id', False))
        for move in production.move_lines:
            operations = self.get_operations(move)
            """
                Se envía a chatarra la cantidad establecida en
                acondicionamiento secundario. Los campos de cantidad servida y
                devuelta son informativos, se usan los del acopio
            """
            for op in operations:
                if op.qty_scrapped > 0:
                    scrap_location_id = self.env['stock.location'].search(
                        [('scrap_location', '=', True)])
                    if not scrap_location_id:
                        raise exceptions.Warning(_('Location not found'),
                                                 _('Scrap location not found.')
                                                 )
                    default_val = {
                        'product_uom_qty': op.qty_scrapped,
                        'served_qty': 0,
                        'returned_qty': 0,
                        'qty_scrapped': 0,
                        'restrict_lot_id': op.lot_id.id,
                        'scrapped': True,
                        'location_dest_id': scrap_location_id[0].id,
                    }
                    move.do_unreserve()
                    move.product_uom_qty -= op.qty_scrapped
                    move.with_context(no_return_operations=True).action_assign()
                    new_move = move.copy(default_val)
                    new_move.action_confirm()
                    new_move.with_context(no_return_operations=True).action_assign()
                    new_move.action_done()
            """
                Para las devoluciones de materiales se usan los datos
                del mismo modelo introducidos en acopio.
            """
            # first_pack_operation = operations[0].move_id.move_orig_ids[0].
            dest_location = move.raw_material_production_id.location_src_id.id
            if move.original_move:
                # Si se ha consumido cuarentena, la cantidad no consumida se
                # devuelve al movimiento del flujo original.
                if move.original_move.state != 'done':
                    dest_location = move.original_move.location_id.id
                    move.original_move.do_unreserve()
                    move.original_move.product_uom_qty += operations[0].hoard_returned_qty
                    originals += move.original_move
                else:
                    dest_location = move.original_move.location_dest_id.id
            move.location_dest_id = dest_location
            if len(operations) == 1:
                move.restrict_lot_id = operations[0].lot_id.id
            elif len(operations) > 1:
                move.restrict_lot_id = operations[0].lot_id.id
                move.do_unreserve()
                move.product_uom_qty = operations[0].hoard_returned_qty
                for op in operations:
                    if op.id == operations[0].id:
                        continue
                    default_val = {
                        'product_uom_qty': op.hoard_returned_qty,
                        'restrict_lot_id': op.lot_id.id,
                        'location_dest_id': dest_location,
                    }
                    new_move = move.copy(default_val)
                    new_move.action_confirm()
                    new_move.with_context(no_return_operations=True).action_assign()
                    new_move.action_done()
                move.with_context(no_return_operations=True).action_assign()
            move.action_done()
        originals.action_assign()
        return res
