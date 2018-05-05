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
from openerp import models, fields, api
from datetime import datetime


class MrpProductionProductLine(models.Model):

    _inherit = 'mrp.production.product.line'

    @api.one
    @api.depends('product_id')
    def _get_stock(self):
        states = {
            'in_rev': 'qty_quality',
            'rejected': 'qty_rejected'
        }
        for state in states:
            lot_ids = self.env['stock.production.lot'].search(
                [('product_id', '=', self.product_id.id),
                 ('state', '=', state)])
            context = dict(self.env.context)
            total = 0
            for lot in lot_ids:
                context['lot_id'] = lot.id
                total += self.product_id._product_available(
                    )[self.product_id.id]['qty_available']
            self[states[state]] = total

    @api.one
    def _get_incoming_date(self):
        moves = self.env['stock.move'].search(
            [('picking_type_id.code', '=', 'incoming'),
             ('product_id', '=', self.product_id.id),
             ('state', 'not in', ['draft', 'cancel', 'done'])])
        if moves:
            dates = [datetime.strptime(x.date_expected, '%Y-%m-%d %H:%M:%S')
                     for x in moves]
            self.incoming_date = min(dates)

    qty_available = fields.Float('Quantity available',
                                 related='product_id.qty_available')
    qty_quality = fields.Float('Quantity on quality', compute='_get_stock')
    qty_rejected = fields.Float('Quantity rejected', compute='_get_stock')
    incoming_qty = fields.Float('Incoming quantity',
                                related='product_id.incoming_qty')
    incoming_date = fields.Date('Incoming date', compute='_get_incoming_date')


class stock_move_consume(models.TransientModel):
    _inherit = 'stock.move.consume'

    @api.model
    def default_get(self, fields):
        res = super(stock_move_consume, self).default_get(fields)
        move = self.env['stock.move'].browse(self.env.context['active_id'])
        if 'restrict_lot_id' in fields:
            res.update({'restrict_lot_id': move.restrict_lot_id.id})
        return res
