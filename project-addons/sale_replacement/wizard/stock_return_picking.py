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

from openerp import models, exceptions
from openerp.tools.translate import _


class stock_return_picking(models.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        record_id = context and context.get('active_id', False) or False
        sale_line_obj = self.pool.get('sale.order.line')
        move_obj = self.pool.get('stock.move')
        pick_obj = self.pool.get('stock.picking')
        uom_obj = self.pool.get('product.uom')
        data_obj = self.pool.get('stock.return.picking.line')
        pick = pick_obj.browse(cr, uid, record_id, context=context)
        data = self.read(cr, uid, ids[0], context=context)
        returned_lines = 0
        # Cancel assignment of existing chained assigned moves
        moves_to_unreserve = []
        to_check_moves = []
        for move in pick.move_lines:
            to_check_moves = [move.move_dest_id] if move.move_dest_id.id else []
            while to_check_moves:
                current_move = to_check_moves.pop()
                if current_move.state not in ('done', 'cancel') and \
                        current_move.reserved_quant_ids:
                    moves_to_unreserve.append(current_move.id)
                split_move_ids = move_obj.search(cr, uid,
                                                 [('split_from', '=',
                                                   current_move.id)],
                                                 context=context)
                if split_move_ids:
                    to_check_moves += move_obj.browse(cr, uid, split_move_ids,
                                                      context=context)

        if moves_to_unreserve:
            move_obj.do_unreserve(cr, uid, moves_to_unreserve, context=context)
            # break the link between moves in order to be able to fix them
            # later if needed
            move_obj.write(cr, uid, moves_to_unreserve,
                           {'move_orig_ids': False}, context=context)

        # Create new picking for returned products
        pick_type_id = pick.picking_type_id.return_picking_type_id and \
            pick.picking_type_id.return_picking_type_id.id or \
            pick.picking_type_id.id
        new_picking = pick_obj.copy(cr, uid, pick.id, {
            'move_lines': [],
            'picking_type_id': pick_type_id,
            'state': 'draft',
            'origin': pick.name,
            'invoice_state': data['invoice_state'],
        }, context=context)

        for data_get in data_obj.browse(cr, uid, data['product_return_moves'],
                                        context=context):
            move = data_get.move_id
            if not move:
                raise exceptions.except_orm(_('Warning !'),
                                            _("You have manually created "
                                              "product lines, please delete "
                                              "them to proceed"))
            new_qty = data_get.quantity
            if new_qty:
                # si es una reposición se controla que la cantidad no pase
                # del total que falta por reponer.
                if move.picking_id and move.picking_id.sale_id and \
                        move.picking_id.sale_id.replacement:
                    used_sale_line = None
                    for line in move.picking_id.sale_id.order_line:
                        if line.product_id.id == data_get.product_id.id and \
                            new_qty <= (line.product_uom_qty -
                                        line.qty_replacement):
                            used_sale_line = line
                    if not used_sale_line:
                        raise exceptions.except_orm(_('Replacement Error !'),
                                                    _("Error in the quantity"
                                                      "of replacement."))
                    qty_replacement = used_sale_line.qty_replacement + new_qty
                    sale_line_obj.write(cr, uid, [used_sale_line.id],
                                        {'qty_replacement': qty_replacement},
                                        context)
                returned_lines += 1
                move_obj.copy(cr, uid, move.id, {
                    'product_id': data_get.product_id.id,
                    'product_uom_qty': new_qty,
                    'product_uos_qty': uom_obj._compute_qty(cr, uid,
                                                            move.product_uom.id,
                                                            new_qty,
                                                            move.product_uos.id),
                    'picking_id': new_picking,
                    'state': 'draft',
                    'location_id': move.location_dest_id.id,
                    'location_dest_id': move.location_id.id,
                    'origin_returned_move_id': move.id,
                    'procure_method': 'make_to_stock',
                    'restrict_lot_id': data_get.lot_id.id,
                    'invoice_state': data['invoice_state'],
                })

        if not returned_lines:
            raise exceptions.except_orm(_('Warning!'),
                                        _("Please specify at least one"
                                          "non-zero quantity."))

        pick_obj.action_confirm(cr, uid, [new_picking], context=context)
        pick_obj.action_assign(cr, uid, [new_picking], context)
        return new_picking, pick_type_id
