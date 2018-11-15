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
from openerp import models, fields, api
from openerp.tools import float_is_zero


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    release_log_ids = fields.One2many('mrp.partial.release.log',
                                      'production_id', 'Partial release log')

    @api.model
    def action_produce(self, production_id, production_qty, production_mode,
                       wiz=False):
        if production_mode == 'only_produce':
            production = self.browse(production_id)
            prod_name = production.name
            procurement_group = self.env['procurement.group'].search(
                [('name', '=', prod_name)], limit=1)
            if not procurement_group:
                procurement_group = self.env['procurement.group'].create(
                    {'name': prod_name})
            self = self.with_context(set_push_group=procurement_group.id)
            # Volvemos a hacer browse para que use el context correcto
            production = self.browse(production_id)
            precision = self.env['decimal.precision'].precision_get(
                'Product Unit of Measure')
            production_qty_uom = self.env['product.uom']._compute_qty(
                production.product_uom.id, production_qty,
                production.product_id.uom_id.id)
            # To produce remaining qty of final product
            produced_products = {}
            for produced_product in production.move_created_ids2:
                if produced_product.scrapped:
                    continue
                if not produced_products.get(produced_product.product_id.id,
                                             False):
                    produced_products[produced_product.product_id.id] = 0
                produced_products[produced_product.product_id.id] += \
                    produced_product.product_qty
            for produce_product in production.move_created_ids:
                subproduct_factor = production._get_subproduct_factor(
                    produce_product.id)
                lot_id = False
                if wiz:
                    lot_id = wiz.lot_id.id
                qty = min(subproduct_factor * production_qty_uom,
                          produce_product.product_qty)
                new_moves = produce_product.action_consume(
                    qty, location_id=produce_product.location_id.id,
                    restrict_lot_id=lot_id)
                new_moves = self.env['stock.move'].browse(new_moves)
                new_moves.write({'production_id': production_id})
                remaining_qty = subproduct_factor * production_qty_uom - qty
                if not float_is_zero(remaining_qty,
                                     precision_digits=precision):
                    extra_move = produce_product.copy(
                        default={'product_uom_qty': remaining_qty,
                                 'production_id': production_id})
                    # Cancelamos disponibilidad de albaranes ya creados
                    # Para que asigne con el nuevo movimiento
                    pickings = (production.move_created_ids +
                                production.move_created_ids2).mapped(
                                    'move_dest_id.picking_id').filtered(
                                        lambda r: r.state == 'assigned')
                    pickings.do_unreserve()
                    extra_move.action_confirm()
                    pickings.rereserve_pick()
                    extra_move.action_done()

        return super(MrpProduction, self).action_produce(
            production_id, production_qty, production_mode, wiz)


class MrpProductionProduce(models.TransientModel):

    _inherit = 'mrp.product.produce'

    mode = fields.Selection(selection_add=[('only_produce', 'only produce')])
