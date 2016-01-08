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
from openerp import models, api


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
                prodlot_id = self.env['stock.production.lot'].with_context(
                    {'product_id': item['product_id'],
                     'partner_id': picking.partner_id.id}).create(
                    {'product_id': item['product_id'],
                     'partner_id': picking.partner_id.id})
                item['lot_id'] = prodlot_id.id
        return res
