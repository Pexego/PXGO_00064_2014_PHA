# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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
from openerp import models, api, fields


class stock_transfer_details(models.TransientModel):
    _inherit = 'stock.transfer_details'


    @api.model
    def default_get(self, fields):
        res = super(stock_transfer_details, self).default_get(fields)
        picking = self.env['stock.picking'].browse(
            self.env.context.get('active_id', False))
        if picking.picking_type_code == 'incoming':
            for item in res.get('item_ids', []):
                if not item['product_id'] or item['lot_id']:
                    continue
                product = self.env['product.product'].browse(item['product_id'])
                item['assigned_lot'] = self.env['stock.transfer_details_items'].get_assigned_lot(product)
        return res

    @api.multi
    def wizard_view(self):
        if self.picking_id.picking_type_code == 'incoming':
            for line in self.item_ids:
                if not line.lot_id:
                    line.assigned_lot = self.env['stock.transfer_details_items'].get_assigned_lot(line.product_id)
        return super(stock_transfer_details, self).wizard_view()


class StockTransferDetailsItems(models.TransientModel):

    _inherit = 'stock.transfer_details_items'

    assigned_lot = fields.Char('Assigned lot')

    @api.multi
    def create_lot(self):
        if self.transfer_id.picking_id.picking_type_code == 'incoming':
                if not self.product_id or self.lot_id:
                    return self.transfer_id.wizard_view()
                prodlot_id = self.env['stock.production.lot'].with_context(
                    {'product_id': self.product_id.id,
                     'partner_id': self.transfer_id.picking_id.partner_id.id}).create(
                    {'product_id': self.product_id.id,
                     'partner_id': self.transfer_id.picking_id.partner_id.id})
                self.write({'lot_id': prodlot_id.id, 'assigned_lot': False})
        return self.transfer_id.wizard_view()

    @api.model
    def get_assigned_lot(self, product):
        sequence = False
        if product and product.sequence_id:
            sequence = product.sequence_id
        else:
            sequence = self.env.ref('stock.sequence_production_lots')
        if sequence:
            d = sequence._interpolation_dict()
            prefix = sequence.prefix and sequence.prefix % d or ''
            suffix = sequence.suffix and sequence.suffix % d or ''
            next_seq = prefix + '%%0%sd' % sequence.padding % sequence.number_next_actual + suffix
            return next_seq
        return False
