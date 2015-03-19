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

from openerp import models, fields, api


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    move_lines = fields.One2many('stock.move', 'raw_material_production_id',
                                 'Products to Consume', readonly=True,
                                 domain=[('state', 'not in',
                                          ('done', 'cancel'))],
                                 states={'draft': [('readonly', False)],
                                         'confirmed': [('readonly', False)]})
    orig_move_ids = fields.One2many('stock.move', 'q_production_id', 'original moves')
    return_operation_ids = fields.One2many('stock.move.return.operations', 'production_id', 'Return operations')
    hoard_picking_id = fields.Many2one(string='hoard picking', related='orig_move_ids.picking_id')

    def _create_previous_move(self, cr, uid, move_id, product, source_location_id, dest_location_id, context=None):
        move = super(MrpProduction, self)._create_previous_move(cr, uid, move_id, product, source_location_id, dest_location_id, context)
        self.pool.get('stock.move').write(cr, uid, move,
            {'q_production_id': context.get('production_id', False)
        }, context=context)
        return move

    @api.model
    def _make_consume_line_from_data(self, production, product, uom_id, qty,
                                     uos_id, uos_qty):
        """
            inherit: Se hereda unicamente para modificar el contexto
                     Ver funcion _create_previous_move
        """
        my_context = dict(self.env.context)
        if production:
            my_context['production_id'] = production.id
        return super(MrpProduction, self.with_context(my_context))._make_consume_line_from_data(production, product,
                                                     uom_id, qty, uos_id,
                                                     uos_qty)


class mrp_product_produce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def on_change_qty(self, cr, uid, ids, product_qty, consume_lines, context=None):
        """
            When changing the quantity of products to be produced it will
            recalculate the number of raw materials needed according
            to the scheduled products and the already consumed/produced products
            It will return the consume lines needed for the products to be produced
            which the user can still adapt
        """
        prod_obj = self.pool.get("mrp.production")
        uom_obj = self.pool.get("product.uom")
        production = prod_obj.browse(cr, uid, context['active_id'], context=context)
        new_consume_lines = []
        for move in production.move_lines:
            for line in move.return_operation_ids:
                new_consume_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.qty - line.returned_qty - line.qty_scrapped,
                    'lot_id': line.lot_id
                }))

        return {'value': {'consume_lines': new_consume_lines}}
