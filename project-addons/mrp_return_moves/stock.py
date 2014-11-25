# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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


class StockMove(models.Model):

    _inherit = "stock.move"

    returned_qty = fields.Float('Returned qty.', help="""Qty. of move that will
                                be returned on produce""")

    served_qty = fields.Float('Served qty',
                              help="Quality system field, no data")

    mrp_prev_move = fields.Boolean('Previous move')

    q_production_id = fields.Many2one('mrp.production', '')

    '''def action_consume(self, cr, uid, ids, product_qty, location_id=False,
                       restrict_lot_id=False, restrict_partner_id=False,
                       consumed_for=False, context=None):
        for move in self.browse(cr, uid, ids, context=context):
            if move.raw_material_production_id and move.returned_qty:
                prev_move_ids = self.search(cr, uid, [('move_dest_id', '=',
                                                       move.id)],
                                            context=context)
                if prev_move_ids:
                    prev_move = self.browse(cr, uid, prev_move_ids[0],
                                            context=context)
                    new_move = self.copy(cr, uid, prev_move.id, {
                        'location_id': prev_move.location_dest_id.id,
                        'location_dest_id': prev_move.location_id.id,
                        'product_uom_qty': move.returned_qty,
                        'picking_id': False,
                        'move_dest_id': False,
                        'raw_material_production_id':
                            move.raw_material_production_id.id,
                        'picking_type_id': False
                    })
                    self.action_done(cr, uid, [new_move], context=context)
        return super(StockMove, self).action_consume(cr, uid, ids, product_qty,
                                                     location_id,
                                                     restrict_lot_id,
                                                     restrict_partner_id,
                                                     consumed_for, context)'''


class stockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.one
    def action_assign(self):
        for move in self.move_lines:
            if move.mrp_prev_move:
                if move.product_uom_qty != move.served_qty:
                    raise exceptions.Warning(_("""Cannot produce because
move quantity %s and served quantity %s don't match""") %
                                             (str(move.product_uom_qty),
                                              str(move.served_qty)))
                if move.returned_qty > 0:
                    move.product_uom_qty = move.served_qty - move.returned_qty
        return super(stockPicking, self).action_assign()
