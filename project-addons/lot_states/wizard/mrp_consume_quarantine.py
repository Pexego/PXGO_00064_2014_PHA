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
    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True)
    line_ids = fields.One2many('mrp.production.consume.quarantine.line',
                               'wizard_id', 'Lots')

    @api.model
    def default_get(self, fields):
        res = super(MrpConsumeQuarantine, self).default_get(fields)
        move_id = self.env.context.get('active_id', [])
        move = self.env['stock.move'].browse(move_id)
        res['product_id'] = move.product_id.id
        lots = self.env['stock.production.lot'].search(
            [('product_id', '=', move.product_id.id), ('state', '=', 'in_rev')
             ])
        lines = []
        my_context = dict(self.env.context)
        my_context['location_id'] = move.warehouse_id.wh_qc_stock_loc_id.id
        for lot in lots:
            my_context['lot_id'] = lot.id
            qty = lot.product_id.with_context(my_context)._product_available()
            qty = qty[lot.product_id.id]['qty_available']
            lines.append((0, 0, {'lot_id': lot.id, 'qty': qty,
                                 'entry_date': lot.entry_quarantine}))
        res['line_ids'] = lines
        return res

    @api.multi
    def consume(self):
        group = self.env.ref('lot_states.mrp_use_quarantine')
        if group not in self.env.user.groups_id:
            raise exceptions.Warning(_('Permission error'),
                                     _('No permission to consume quarantine'))
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


class MrpConsumeQuarantineLine(models.TransientModel):

    _name = 'mrp.production.consume.quarantine.line'

    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    wizard_id = fields.Many2one('mrp.production.consume.quarantine', 'wizard')
    qty = fields.Float('Quantity')
    entry_date = fields.Date('Entry quarantine')
