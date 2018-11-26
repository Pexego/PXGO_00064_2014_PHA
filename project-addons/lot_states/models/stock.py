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

    pick_aux = fields.Many2one('stock.picking',
                               'Auxiliar picking for control lot states')


class StockMove(models.Model):

    _inherit = 'stock.move'

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
    def _get_receipt_locations(self):
        self.ensure_one()
        warehouse = self.picking_type_id.warehouse_id
        input_locs = warehouse.wh_input_stock_loc_id._get_child_locations()
        quality_locs = warehouse.wh_qc_stock_loc_id._get_child_locations()
        stock_locs = warehouse.lot_stock_id._get_child_locations()
        source_location = self.location_id
        dest_location = self.location_dest_id
        return input_locs, quality_locs, stock_locs, source_location, \
            dest_location

    @api.multi
    def action_done(self):
        errors = ''
        for move in self:
            if not move.picking_type_id:
                continue
            input_locs, quality_locs, stock_locs, source_location, \
                dest_location = move._get_receipt_locations()
            for operation in move.linked_move_operation_ids:
                lot_id = operation.operation_id.lot_id
                if source_location in quality_locs and \
                        dest_location in stock_locs:
                    if lot_id.state not in ('revised', 'approved'):
                        errors += '\n' + _('Cannot move to stock, the lot %s'
                                           ' is in %s state') % \
                                         (lot_id.name, lot_id.state)
                elif source_location in input_locs and  \
                        dest_location in stock_locs:
                    lot_id.signal_workflow('direct_approved')
        if errors:
            raise exceptions.Warning(_('Lot error'), errors)
        return super(StockMove, self).action_done()


class stock_transfer_details_items(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    acceptance_date = fields.Date('Acceptance date', readonly=True,
                                  related='lot_id.acceptance_date')


class stock_location(models.Model):

    _inherit = 'stock.location'

    @api.multi
    def _get_child_locations(self):
        self.ensure_one()
        return self.search([('id', 'child_of', self.id)])
