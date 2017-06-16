# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. Department. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, tools, api


class StockLotMove(models.Model):
    _name = 'stock.lot.move'
    _auto = False

    lot_id = fields.Many2one(comodel_name='stock.production.lot')
    move_id = fields.Many2one(comodel_name='stock.move')
    date = fields.Datetime(related='move_id.date')
    qty = fields.Float(string='Quantity')
    type = fields.Char(compute='_check_type')
    product_uom_id = fields.Many2one(comodel_name='product.uom',
                                     related='move_id.product_uom')
    location_id = fields.Many2one(comodel_name='stock.location',
                                  related='move_id.location_id')
    destination_id = fields.Many2one(comodel_name='stock.location',
                                     related='move_id.location_dest_id')
    partner_id = fields.Many2one(string='Partner',
                                 comodel_name='res.partner',
                                 related='move_id.picking_id.partner_id')
    picking_id = fields.Many2one(string='Picking',
                                 comodel_name='stock.picking',
                                 related='move_id.picking_id')

    @api.one
    def _check_type(self):
        if (self.location_id.usage in
                ['internal', 'view', 'procurement', 'transit']) and\
           (self.destination_id.usage in
                ['customer', 'inventory', 'supplier', 'production']):
            self.type = 'output'
        elif (self.location_id.usage in
                  ['customer', 'inventory', 'supplier', 'production']) and\
             (self.destination_id.usage in
                  ['internal', 'view', 'procurement', 'transit']):
            self.type = 'input'
        else:
            self.type = 'internal'

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
            create view %s as (
            	select
                    row_number() over() as id,
                    lot_moves.lot_id,
                    lot_moves.move_id,
                    lot_moves.qty
                from (
	                select
	                    spl.id lot_id,
	                    sqmr.move_id move_id,
	                    sum(sq.qty) qty
	                from stock_production_lot spl
	                join stock_quant sq on sq.lot_id = spl.id
	                join stock_quant_move_rel sqmr on sqmr.quant_id = sq.id
	                group by 1, 2
	            ) as lot_moves
            )
        """ % (self._table,))


class LotTracking(models.Model):
    _name = 'lot.tracking'
    _description = ''
    _rec_name = 'product_id'

    product_id = fields.Many2one(comodel_name='product.product',
                                 domain="[('sequence_id', '!=', False)]")
    lot_id = fields.Many2one(comodel_name='stock.production.lot',
                             domain="[('product_id', '=', product_id)]")
    type_of_move = fields.Selection(string='Type of moves',
        selection=[('all', 'All movements'),('io', 'Inputs & Outputs')],
        default='io', required=True)

    lot_move_ids = fields.One2many(comodel_name='stock.lot.move',
                                   compute='_get_lot_moves')
    total = fields.Float(string='Total', compute='_get_total')
    company_id = fields.Many2one(comodel_name='res.company',
                                 related='product_id.company_id')

    @api.onchange('product_id')
    def clear_lot(self):
        self.lot_id = False

    @api.one
    def _get_lot_moves(self):
        if self.type_of_move == 'all':
            self.lot_move_ids = self.env['stock.lot.move'].\
                search([('lot_id', '=', self.lot_id.id)])
        else:
            self.lot_move_ids = self.env['stock.lot.move'].\
                search([
                    '&',
                    ('lot_id', '=', self.lot_id.id),
                    '|',
                    '&',
                    ('location_id.usage', 'in', ('internal', 'view', 'procurement', 'transit')),
                    ('destination_id.usage', 'in', ('customer', 'inventory', 'supplier', 'production')),
                    '&',
                    ('location_id.usage', 'in', ('customer', 'inventory', 'supplier', 'production')),
                    ('destination_id.usage', 'in', ('internal', 'view', 'procurement', 'transit'))
                ])

    @api.one
    def _get_total(self):
        total = 0
        for move in self.lot_move_ids:
            if move.type == 'input':
                total += move.qty
            elif move.type == 'output':
                total -= move.qty
        self.total = total

    @api.onchange('lot_id', 'type_of_move')
    def get_lot_moves(self):
        self._get_lot_moves()
        self._get_total()
