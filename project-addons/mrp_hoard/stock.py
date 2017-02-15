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
import openerp.addons.decimal_precision as dp


class StockMoveReturnOperations(models.Model):

    _name = 'stock.move.return.operations'

    product_id = fields.Many2one('product.product', 'Product')
    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True)
    qty = fields.Float('Quantity',
                       digits=dp.get_precision('Product Unit of Measure'))
    move_id = fields.Many2one('stock.move', 'Move')
    production_id = fields.Many2one('mrp.production', 'Production')
    product_uom = fields.Many2one('product.uom', 'UoM')
    """Informative fields"""
    served_qty = fields.Float('Served qty',
                              help="Quality system field, no data",
                              digits=dp.get_precision(
                                   'Product Unit of Measure'))
    returned_qty = fields.Float('Returned qty', help="""Qty. of move that will
be returned on produce""", digits=dp.get_precision('Product Unit of Measure'))
    qty_used = fields.Float('Qty used',
                            digits=dp.get_precision('Product Unit of Measure'))
    qty_scrapped = fields.Float('Qty scrapped',
                                digits=dp.get_precision(
                                    'Product Unit of Measure'))
    initials = fields.Char('Initials')
    initials_return = fields.Char('Initials')
    initials_acond = fields.Char('Initials')
    used_lot = fields.Char('Use lot')

    """Fields of hoard used for return excess material"""
    hoard_served_qty = fields.Float('Served qty',
                                    help="Quality system field, no data",
                                    digits=dp.get_precision(
                                        'Product Unit of Measure'))
    hoard_returned_qty = fields.Float('Returned qty',
                                      help="""Qty. of move that will
be returned on produce""", digits=dp.get_precision('Product Unit of Measure'))
    hoard_initials = fields.Char('Initials')
    hoard_initials_return = fields.Char('Initials')
    acceptance_date = fields.Date('Acceptance date', readonly=True,
                                  related='lot_id.acceptance_date')

    @api.model
    def create(self, vals):
        """
            Se rellenan los campos que faltan con el lote
        """
        lot_id = int(vals.get('lot_id', False))
        lot = self.env['stock.production.lot'].browse(lot_id)
        if not vals.get('product_id', False):
            vals['product_id'] = lot.product_id.id
        if not vals.get('product_uom', False):
            vals['product_uom'] = lot.product_id.uom_id.id
        vals['lot_id'] = lot_id
        return super(StockMoveReturnOperations, self).create(vals)


class StockMove(models.Model):

    _inherit = 'stock.move'

    is_hoard_move = fields.Boolean('Is hoard move',
                                   compute='_get_is_hoard_move')
    original_move = fields.Many2one('stock.move', 'Original move')
    return_operation_ids = fields.One2many('stock.move.return.operations',
                                           'move_id', 'Return operations')
    return_production_move = fields.Boolean('return production move',
                                            copy=False)

    @api.one
    @api.depends('raw_material_production_id')
    def _get_is_hoard_move(self):
        self.is_hoard_move = self.move_dest_id and \
            self.move_dest_id.raw_material_production_id or False

    @api.multi
    def action_assign(self):
        """
            Se actualizan los registros de return operations unicamente si
            los movimientos corresponden a una produccion, o si es un acopio.
        """
        super(StockMove, self).action_assign()
        if self.env.context.get('no_return_operations', False):
            return
        q_lot_ids = []
        for move in self:
            if move.raw_material_production_id or  \
                    (move.move_dest_id and
                     move.move_dest_id.raw_material_production_id):
                op_move = move
                if move.move_dest_id:
                    op_move = move.move_dest_id
                if op_move.return_operation_ids:
                    op_move.return_operation_ids.unlink()

                quants = self.env['stock.quant'].read_group(
                    [('reservation_id', '=', move.id)], ['lot_id', 'qty'],
                    ['lot_id'])
                for quant in quants:
                    lot = quant['lot_id']
                    if lot:
                        q_lot_ids.append(lot[0])
                    operation = self.env['stock.move.return.operations'].search(
                        [('move_id', '=', op_move.id),
                         ('lot_id', '=', lot and lot[0] or False)])
                    operation_dict = {
                        'product_id': op_move.product_id.id,
                        'lot_id': lot and lot[0] or False,
                        'qty': quant['qty'],
                        'product_uom': move.product_uom.id,
                        'move_id': op_move.id,
                        'production_id': op_move.raw_material_production_id.id
                    }
                    self.env['stock.move.return.operations'].create(operation_dict)
