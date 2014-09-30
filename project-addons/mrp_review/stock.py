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

from openerp import models, api, _


class StockMove(models.Model):

    _inherit = 'stock.move'

    def action_consume(self, cr, uid, ids, product_qty, location_id=False, restrict_lot_id=False, restrict_partner_id=False,
                       consumed_for=False, context=None):
        """ Consumed product with specific quantity from specific source location.
        @param product_qty: Consumed product quantity
        @param location_id: Source location
        @param restrict_lot_id: optionnal parameter that allows to restrict the choice of quants on this specific lot
        @param restrict_partner_id: optionnal parameter that allows to restrict the choice of quants to this specific partner
        @param consumed_for: optionnal parameter given to this function to make the link between raw material consumed and produced product, for a better traceability
        @return: Consumed lines
        """
        if context is None:
            context = {}
        res = []
        production_obj = self.pool.get('mrp.production')
        uom_obj = self.pool.get('product.uom')

        if product_qty <= 0:
            raise osv.except_osv(_('Warning!'), _('Please provide proper quantity.'))
        #because of the action_confirm that can create extra moves in case of phantom bom, we need to make 2 loops
        ids2 = []
        for move in self.browse(cr, uid, ids, context=context):
            if move.state == 'draft':
                ids2.extend(self.action_confirm(cr, uid, [move.id], context=context))
            else:
                ids2.append(move.id)

        for move in self.browse(cr, uid, ids2, context=context):
            move_qty = move.product_qty
            uom_qty = uom_obj._compute_qty(cr, uid, move.product_id.uom_id.id, product_qty, move.product_uom.id)
            if move_qty <= 0:
                raise osv.except_osv(_('Error!'), _('Cannot consume a move with negative or zero quantity.'))
            quantity_rest = move.product_qty - uom_qty
            if quantity_rest > 0:
                ctx = context.copy()
                if location_id:
                    ctx['source_location_id'] = location_id
                new_mov = self.split(cr, uid, move, move_qty - quantity_rest, restrict_lot_id=restrict_lot_id, restrict_partner_id=restrict_partner_id, context=ctx)
                self.write(cr, uid, new_mov, {'consumed_for': consumed_for}, context=context)
                res.append(new_mov)
            else:
                res.append(move.id)
                if location_id:
                    self.write(cr, uid, [move.id], {'location_id': location_id, 'restrict_lot_id': restrict_lot_id,
                                                    'restrict_partner_id': restrict_partner_id,
                                                    'consumed_for': consumed_for}, context=context)
            if not context.get('final', False):
                self.action_done(cr, uid, res, context=context)
            production_ids = production_obj.search(cr, uid, [('move_lines', 'in', [move.id])])
            production_obj.signal_workflow(cr, uid, production_ids, 'button_produce')
            for new_move in res:
                if new_move != move.id:
                    #This move is not already there in move lines of production order
                    production_obj.write(cr, uid, production_ids, {'move_lines': [(4, new_move)]})
        return res
