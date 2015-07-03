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
from openerp import models, fields, api


class StockMoveReturnOperations(models.Model):

    _name = 'stock.move.return.operations'

    product_id = fields.Many2one('product.product', 'Product')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    qty = fields.Float('Quantity')
    move_id = fields.Many2one('stock.move', 'Move')
    production_id = fields.Many2one('mrp.production', 'Production')
    product_uom = fields.Many2one('product.uom', 'UoM')
    served_qty = fields.Float('Served qty',
                              help="Quality system field, no data")
    returned_qty = fields.Float('Returned qty', help="""Qty. of move that will
                                be returned on produce""")
    qty_used = fields.Float('Qty used')
    qty_scrapped = fields.Float('Qty scrapped')
    acceptance_date = fields.Date('Acceptance date')
    initials = fields.Char('Initials')
    initials_return = fields.Char('Initials')
    initials_acond = fields.Char('Initials')
    used_lot = fields.Char('Use lot')


class StockMove(models.Model):

    _inherit = 'stock.move'

    return_operation_ids = fields.One2many('stock.move.return.operations',
                                           'move_id', 'Return operations')
    is_hoard_move = fields.Boolean('Is hoard move',
                                   compute='_get_is_hoard_move')
    original_move = fields.Many2one('stock.move', 'Original move')

    @api.one
    @api.depends('raw_material_production_id')
    def _get_is_hoard_move(self):
        self.is_hoard_move = self.move_dest_id and \
            self.move_dest_id.raw_material_production_id or False

    @api.multi
    def action_assign(self):
        """
            Se actualizan los registros de return operations unicamente si
            los movimientos corresponden a una produccion
        """

        super(StockMove, self).action_assign()
        if self.env.context.get('no_return_operations', False):
            return
        q_lot_ids = []
        for move in self:
            if not move.raw_material_production_id:
                continue
            quants = self.env['stock.quant'].read_group(
                [('reservation_id', '=', move.id)], ['lot_id', 'qty'],
                ['lot_id'])
            for quant in quants:
                lot = quant['lot_id']
                if lot:
                    q_lot_ids.append(lot[0])
                operation = self.env['stock.move.return.operations'].search(
                    [('move_id', '=', move.id),
                     ('lot_id', '=', lot and lot[0] or False)])
                if operation:
                    if operation.qty != quant['qty']:
                        operation.qty = quant['qty']
                    continue
                operation_dict = {
                    'product_id': move.product_id.id,
                    'lot_id': lot and lot[0] or False,
                    'qty': quant['qty'],
                    'product_uom': move.product_uom.id,
                    'move_id': move.id,
                    'production_id': move.raw_material_production_id.id
                }
                self.env['stock.move.return.operations'].create(operation_dict)
            for operation in move.return_operation_ids:
                if operation.lot_id.id not in q_lot_ids:
                    operation.unlink()
