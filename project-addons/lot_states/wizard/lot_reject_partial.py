# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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


class stock_lot_reject_partial(models.TransientModel):

    _name = 'stock.lot.reject.partial'

    quantity = fields.Float('Quantity')

    @api.multi
    def reject(self):
        """
            Solo se hacen rechazos parciales para productos que no se consumen
                en producción mientras están en cuarentena.
        """
        location_rejected = self.env.ref('lot_states.stock_location_rejected')
        lot = self.env['stock.production.lot'].browse(
            self.env.context.get('active_id', False))
        if not lot:
            raise exceptions.Warning(_('Lot error'), _('Lot not found.'))
        moves = self.env['stock.move']
        rejected_picking = False
        for quant in lot.quant_ids:
            if quant.reservation_id.location_dest_id != location_rejected and \
                    quant.reservation_id not in moves:
                moves += quant.reservation_id
            elif quant.reservation_id.location_dest_id == location_rejected \
                    and not rejected_picking:
                rejected_picking = quant.reservation_id.picking_id
        if len(moves) == 1:
            if moves.product_uom_qty <= self.quantity:
                raise exceptions.Warning(
                    _('Quantity error'),
                    _('For reject the complete lot use the appropiate means'))
            new_qty = moves.product_uom_qty - self.quantity
            moves.do_unreserve()
            moves.product_uom_qty = new_qty
            moves.change_qty_chain(new_qty)
            if rejected_picking:
                new_picking = rejected_picking
            else:
                new_picking = moves.picking_id.copy({'move_lines': False})
            new_move = moves.copy(
                {'location_dest_id': location_rejected.id,
                 'restrict_lot_id': lot.id, 'move_dest_id': False,
                 'picking_id': new_picking.id,
                 'product_uom_qty': self.quantity})
            new_move.action_confirm()
            new_move.action_assign()
            moves.action_assign()
        elif len(moves) > 1:
            raise exceptions.Warning(_('Reject error'),
                                     _('You can not partially reject a lot \
used in production'))
        return {'type': 'ir.actions.act_window_close'}
