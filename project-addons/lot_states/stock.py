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


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    pick_aux = fields.Many2one('stock.picking', 'Auxiliar picking for control lot states')


class StockMove(models.Model):

    _inherit = 'stock.move'

    original_move = fields.Many2one('stock.move', 'Original move')


    def cancel_chain(self):
        '''
            Se cancelan los movimientos encadenados.
        '''
        if self.move_dest_id:
            self.move_dest_id.action_cancel()
            self.move_dest_id.cancel_chain()

    def change_qty_chain(self, new_qty):
        '''
            Se modifica la cantidad en todos los movimientos encadenados.
        '''
        if self.move_dest_id:
            self.move_dest_id.product_uom_qty = new_qty
            self.move_dest_id.change_qty_chain(new_qty)

    @api.multi
    def action_done(self):
        for move in self:
            input_loc = move.picking_type_id.warehouse_id.wh_input_stock_loc_id
            quality_loc = move.picking_type_id.warehouse_id.wh_qc_stock_loc_id
            stock_loc = move.picking_type_id.warehouse_id.lot_stock_id
            for operation in move.linked_move_operation_ids:
                lot_id = operation.operation_id.lot_id
                if move.location_id.id == input_loc.id and \
                        move.location_dest_id.id == quality_loc.id:
                    if lot_id.state != 'in_rev':
                        raise exceptions.Warning(
                            _('Lot error'),
                            _('Cannot move to quality control, the lot %s is \
in %s state') % (lot_id.name, lot_id.state))
                elif move.location_id.id == quality_loc.id and \
                        move.location_dest_id.id == stock_loc.id:
                    if lot_id.state != 'approved':
                        raise exceptions.Warning(
                            _('Lot error'),
                            _('Cannot move to stock, the lot %s is in %s \
state') % (lot_id.name, lot_id.state))
                elif move.location_id.id == input_loc.id and \
                        move.location_dest_id.id == stock_loc.id:
                    lot_id.signal_workflow('direct_approved')
        return super(StockMove, self).action_done()


class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    acceptance_date = fields.Date('Acceptance date', readonly=True, related='lot_id.acceptance_date')
