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
from openerp import models, api, fields, _


class StockReturnPicking(models.Model):
    _inherit = 'stock.return.picking'

    has_partials_transferred_or_invoiced = fields.Boolean()

    @api.model
    def default_get(self, fields):
        res = super(StockReturnPicking, self).default_get(fields)
        picking_ids = self.env.context.get('active_ids', False)
        picking = self.env['stock.picking'].browse(picking_ids)
        res['has_partials_transferred_or_invoiced'] = \
            picking.has_partials_transferred_or_invoiced
        return res

    @api.multi
    def revert_transfer_and_recreate_picking(self):
        picking_id = self.env.context.get('active_id', False)
        picking = self.env['stock.picking'].browse(picking_id)

        # Transfer new created picking with returns
        revert_picking_id, pick_type_id = self._create_returns()
        revert_picking = picking.browse(revert_picking_id)
        # Set destination location as origin location of
        # returned move pack operation
        for move in revert_picking.move_lines:
            if move.origin_returned_move_id and \
                len(move.origin_returned_move_id.linked_move_operation_ids) > 0:
                move.location_dest_id = move.origin_returned_move_id.\
                           linked_move_operation_ids[0].operation_id.location_id
        revert_picking.do_transfer()

        # Recreate picking
        new_picking = picking.copy({'move_lines': []})

        # Set invoicing policy for origin picking as in revert picking
        picking.invoice_state = revert_picking.invoice_state

        # Remove expedition for original picking
        if picking.expedition_id:
            picking.expedition_id.unlink()

        # Recollect original moves
        origin_moves = self.env['stock.move']
        for move in picking.move_lines:
            origin_moves += move
        for partial_picking in picking.partial_ids:
            for move in partial_picking.move_lines:
                origin_moves += move
            partial_picking.action_cancel()  # Cancel partial pickings

        # Clear previously existing auxiliary procurements
        procurements = self.env['procurement.order.aux']
        for move in origin_moves:
            procurement = procurements.search(
                    [('procurement_id', '=', move.procurement_id.id)])
            if procurement:
                procurement.unlink()

        # Recover affected procurements and quantities
        procurement_ids = []
        for move in origin_moves:
            procurement = procurements.search(
                    [('procurement_id', '=', move.procurement_id.id)])
            if not procurement:
                procurement = procurements.create(
                        {'procurement_id': move.procurement_id.id})
                procurement_ids.append(procurement.id)
            procurement.uom_qty += move.product_uom_qty
            procurement.uos_qty += move.product_uos_qty

        # Create moves from original procurements and reset status
        moves = self.env['stock.move']
        for procurement in procurements.browse(procurement_ids):
            sale_line = procurement.sale_line_id
            new_move = moves.create({
                'group_id': procurement.group_id.id,
                'invoice_state': procurement.invoice_state,
                'location_dest_id': procurement.location_id.id,
                'location_id': procurement.move_ids[0].location_id.id,
                'name': procurement.name,
                'origin': procurement.origin,
                'partner_id': procurement.partner_dest_id.id,
                'picking_id': new_picking.id,
                'picking_type_id': new_picking.picking_type_id.id,
                'price_unit': sale_line.price_unit,
                'priority': procurement.priority,
                'procure_method': 'make_to_stock',
                'procurement_id': procurement.procurement_id.id,
                'product_id': procurement.product_id.id,
                'product_uom': procurement.product_uom.id,
                'product_uom_qty': procurement.uom_qty,
                'product_uos': procurement.product_uos.id,
                'product_uos_qty': procurement.uos_qty,
                'rule_id': procurement.rule_id.id,
                'state': 'draft',
                'warehouse_id': procurement.warehouse_id.id,
            })
            procurement.write({
                'move_dest_id': new_move.id,
                'state': 'running',
            })

        # Confirm picking
        new_picking.action_confirm()

        # Show new created picking
        return {
            'name': _('New picking'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': new_picking.id,
            'context': {},
        }
