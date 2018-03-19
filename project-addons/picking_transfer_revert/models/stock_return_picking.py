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
        pick_type_id = picking.picking_type_id.return_picking_type_id and \
                       picking.picking_type_id.return_picking_type_id.id or \
                       picking.picking_type_id.id

        revert_picking = picking.copy({
            'move_lines': [],
            'picking_type_id': pick_type_id,
            'state': 'draft',
            'origin': picking.name,
        })

        for pack_operation in picking.pack_operation_ids:
            revert_picking.move_lines.create({
                'picking_id': revert_picking.id,
                'picking_type_id': pick_type_id,
                'name': pack_operation.product_id.name,
                'warehouse_id': picking.picking_type_id.warehouse_id.id,
                'location_id': pack_operation.location_dest_id.id,
                'location_dest_id': pack_operation.location_id.id,
                'product_id': pack_operation.product_id.id,
                'product_uom': pack_operation.product_uom_id.id,
                'product_uom_qty': pack_operation.product_qty,
                'lot_ids': pack_operation.lot_id.id,
                'restrict_lot_id': pack_operation.lot_id.id,
                'procure_method': 'make_to_stock',
                'invoice_state': revert_picking.invoice_state,
                'state': 'draft'
            })

        revert_picking.action_confirm()
        revert_picking.action_assign()
        revert_picking.do_transfer()
        revert_picking.group_id = picking.group_id

        # Recreate picking
        new_picking = picking.copy({'move_lines': []})

        # Set invoicing policy for origin picking as in revert picking
        picking.invoice_state = revert_picking.invoice_state

        # Remove expedition for original picking
        if picking.expedition_id:
            picking.expedition_id.unlink()

        # Collect original moves
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
