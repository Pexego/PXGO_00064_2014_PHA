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


class MrpConsumeQuarantine(models.TransientModel):

    _name = 'mrp.production.consume.quarantine'

    product_id = fields.Many2one('product.product', 'Product')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')

    @api.model
    def default_get(self, fields):
        res = super(MrpConsumeQuarantine, self).default_get(fields)
        move_id = self.env.context.get('active_id', [])
        move = self.env['stock.move'].browse(move_id)
        res['product_id'] = move.product_id.id
        return res

    @api.multi
    def consume(self):
        move_id = self.env.context.get('active_id', [])
        move = self.env['stock.move'].browse(move_id)
        quality_location = move.warehouse_id.wh_qc_stock_loc_id
        move.restrict_lot_id = self.lot_id.id

        previous_move = self.env['stock.move'].search([('move_dest_id', '=',
                                                        move.id)])
        previous_move.restrict_lot_id = self.lot_id.id
        previous_move.location_id = move.warehouse_id.wh_qc_stock_loc_id.id
        previous_move.write({'restrict_lot_id': self.lot_id.id,
                             'location_id': quality_location.id})

        read_domain = [('location_id', '=', quality_location.id),
                       ('product_id', '=', move.product_id.id),
                       ('lot_id', '=', self.lot_id.id)]
        q_quants = self.env['stock.quant'].read_group(
            read_domain, ['reservation_id', 'qty'], ['reservation_id'])
        q_move = False
        for quant in q_quants:
            if quant['qty'] > move.product_uom_qty:
                move_id = quant['reservation_id'][0]
                q_move = self.env['stock.move'].browse(move_id)
                break
        if q_move:
            q_move.do_unreserve()
            q_move.product_uom_qty -= previous_move.product_uom_qty
            q_move.action_assign()
            previous_move.original_move = move.original_move = q_move
        else:
            raise exceptions.Warning(_('quarantine error'),
                                     _('Not found the move from quarantine'))
        move.raw_material_production_id.final_lot_id.write(
            {'state_depends': [(4, self.lot_id.id)]})
        return True
