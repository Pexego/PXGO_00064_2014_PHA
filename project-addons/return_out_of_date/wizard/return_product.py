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
from openerp import models, fields, api, exceptions, _


class ReturnOutDateLine(models.TransientModel):

    _name = 'return.out.date.line'

    def _get_uom(self):
        return self.env.ref('product.product_uom_unit').id

    product_id = fields.Many2one('product.product', 'Product', required=True)
    quantity = fields.Float('Quantity', required=True)
    uom_id = fields.Many2one('product.uom', 'UoM', required=True,
                             default=_get_uom)
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    wizard_id = fields.Many2one('return.out.date', 'Wizard')


class ReturnOutDate(models.TransientModel):

    _name = 'return.out.date'

    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    return_lines = fields.One2many('return.out.date.line', 'wizard_id',
                                   'Lines')

    @api.multi
    def return_product(self):
        warehouse = self.env['stock.warehouse'].search([('company_id', '=', self.env.user.company_id.id)])
        warehouse = warehouse and warehouse[0]
        picking_type = warehouse.out_of_date_type_id
        if not picking_type:
            raise exceptions.Warning(_('Configuration error'), _('The warehouse not have a out of date picking type'))
        location = picking_type.default_location_src_id
        location_dest = picking_type.default_location_dest_id
        moves = self.env['stock.move']
        for line in self.return_lines:
            move_vals = {
                'location_id': location.id,
                'location_dest_id': location_dest.id,
                'product_id': line.product_id.id,
                'name': line.product_id.name,
                'product_uom_qty': line.quantity,
                'product_uom': line.uom_id.id,
                'restrict_lot_id': line.lot_id.id
            }
            moves += self.env['stock.move'].create(move_vals)

        picking_vals = {
            'partner_id': self.partner_id.id,
            'picking_type_id': picking_type.id,
            'move_lines': [(4, x.id) for x in moves]
        }
        picking = self.env['stock.picking'].create(picking_vals)
        picking.action_confirm()
        for move in picking.move_lines:
            if move.restrict_lot_id:
                move.with_context(search_quant_by_partner=self.partner_id.id).action_assign()
            else:
                move.force_assign()
        picking.with_context(no_track=True, search_quant_by_partner=self.partner_id.id).do_transfer()
        return {'type': 'ir.actions.act_window_close'}
