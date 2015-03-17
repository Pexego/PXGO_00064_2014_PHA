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


class StockMoveReturnOperations(models.Model):

    _name = 'stock.move.return.operations'

    product_id = fields.Many2one('product.product', 'Product')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    qty = fields.Float('Quantity')
    move_id = fields.Many2one('stock.move', 'Move')
    picking_id = fields.Many2one('stock.picking', 'Picking')
    production_id = fields.Many2one('mrp.production', 'Production')
    returned_qty = fields.Float('Returned qty', help="""Qty. of move that will
                                be returned on produce""")
    product_uom = fields.Many2one('product.uom', 'UoM')
    acceptance_date = fields.Date('Acceptance date')
    initials = fields.Char('Initials')
    initials_return = fields.Char('Initials')

    served_qty = fields.Float('Served qty',
                              help="Quality system field, no data")


class StockMove(models.Model):

    _inherit = "stock.move"

    q_production_id = fields.Many2one('mrp.production', '')

    changed_qty_return = fields.Boolean('changed_qty_return')

    return_operation_ids = fields.One2many('stock.move.return.operations',
                                           'move_id', 'Return operations')
    have_returns = fields.Boolean('Have returns', compute='_get_have_returns')

    @api.multi
    def _get_have_returns(self):
        for move in self:
            have_returns = False
            for operation in move.return_operation_ids:
                if operation.returned_qty > 0:
                    have_returns = True
            move.have_returns = have_returns


    @api.multi
    def action_assign(self):
        super(StockMove, self).action_assign()
        for move in self:
            if move.return_operation_ids and not self.env.context.get('recompute_return_operations', False):
                continue
            move.return_operation_ids.unlink()
            quants = self.env['stock.quant'].read_group(
                [('reservation_id', '=', move.id)], ['lot_id', 'qty'],
                ['lot_id'])
            for quant in quants:
                operation_dict = {
                    'product_id': move.product_id.id,
                    'lot_id': quant['lot_id'][0],
                    'qty': quant['qty'],
                    'product_uom': move.product_uom.id,
                    'move_id': move.id,
                    'picking_id': move.picking_id.id
                }
                self.env['stock.move.return.operations'].create(operation_dict)



class stockPicking(models.Model):

    _inherit = 'stock.picking'

    return_operation_ids = fields.One2many('stock.move.return.operations', 'picking_id', 'return operations')

    @api.multi
    def do_enter_transfer_details(self):
        """
            Se sobreescribe la funcion para evitar problemas con el contexto.
            Se recorren los movimientos, si hay devoluciones se parte en varios movimientos, 1 por cada lote
            con cantidad final y restringiendo lote.
        """
        for move in self.move_lines:
            total_return = 0.0
            if move.have_returns:
                dest_move = move.move_dest_id
                move.do_unreserve()
                for operation in move.return_operation_ids:
                    if operation.returned_qty > operation.served_qty:
                        raise exceptions.Warning(_(''), _(''))
                    elif operation.returned_qty == operation.served_qty:
                        continue
                    total_return += operation.returned_qty
                    new_move = move.copy(
                    {'restrict_lot_id': operation.lot_id.id,
                     'product_uom_qty': operation.served_qty - operation.returned_qty,
                     'move_dest_id': move.move_dest_id.id})
                    new_move.action_confirm()
                    new_move.with_context(recompute_return_operations=False).action_assign()
                    operation.move_id = new_move.id
                move.move_dest_id = False
                move.action_cancel()
                if dest_move:
                    dest_move.product_uom_qty -= total_return
        created = self.env['stock.transfer_details'].with_context(
            {'active_model': self._name,
                'active_ids': self._ids,
                'active_id': len(self) and self[0].id or False
            }).create(
            {'picking_id': len(self) and self[0].id or False})
        return created.wizard_view()
