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

from openerp import models, fields


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    move_lines = fields.One2many('stock.move', 'raw_material_production_id',
                                 'Products to Consume', readonly=True,
                                 domain=[('state', 'not in',
                                          ('done', 'cancel'))],
                                 states={'draft': [('readonly', False)],
                                         'confirmed': [('readonly', False)]})
    orig_move_ids = fields.One2many('stock.move', 'q_production_id', 'original moves')

    def _create_previous_move(self, cr, uid, move_id, product, source_location_id, dest_location_id, context=None):
        '''
        When the routing gives a different location than the raw material location of the production order,
        we should create an extra move from the raw material location to the location of the routing, which
        precedes the consumption line (chained).  The picking type depends on the warehouse in which this happens
        and the type of locations.
        '''
        loc_obj = self.pool.get("stock.location")
        stock_move = self.pool.get('stock.move')
        type_obj = self.pool.get('stock.picking.type')
        # Need to search for a picking type
        move = stock_move.browse(cr, uid, move_id, context=context)
        src_loc = loc_obj.browse(cr, uid, source_location_id, context=context)
        dest_loc = loc_obj.browse(cr, uid, dest_location_id, context=context)
        code = stock_move.get_code_from_locs(cr, uid, move, src_loc, dest_loc, context=context)
        if code == 'outgoing':
            check_loc = src_loc
        else:
            check_loc = dest_loc
        wh = loc_obj.get_warehouse(cr, uid, check_loc, context=context)
        domain = [('code', '=', code)]
        if wh:
            domain += [('warehouse_id', '=', wh)]
        types = type_obj.search(cr, uid, domain, context=context)
        move = stock_move.copy(cr, uid, move_id, default = {
            'location_id': source_location_id,
            'location_dest_id': dest_location_id,
            'procure_method': self._get_raw_material_procure_method(cr, uid, product, context=context),
            'raw_material_production_id': False,
            'move_dest_id': move_id,
            'picking_type_id': types and types[0] or False,
            'mrp_prev_move': True,
            'q_production_id': context.get('production_id', False)
        }, context=context)
        return move

    def _make_consume_line_from_data(self, cr, uid, production, product, uom_id, qty, uos_id, uos_qty, context=None):
        stock_move = self.pool.get('stock.move')
        loc_obj = self.pool.get('stock.location')
        # Internal shipment is created for Stockable and Consumer Products
        if product.type not in ('product', 'consu'):
            return False
        # Take routing location as a Source Location.
        source_location_id = production.location_src_id.id
        prod_location_id = source_location_id
        prev_move= False
        if production.bom_id.routing_id and production.bom_id.routing_id.location_id and production.bom_id.routing_id.location_id.id != source_location_id:
            source_location_id = production.bom_id.routing_id.location_id.id
            prev_move = True

        destination_location_id = production.product_id.property_stock_production.id
        move_id = stock_move.create(cr, uid, {
            'name': production.name,
            'date': production.date_planned,
            'product_id': product.id,
            'product_uom_qty': qty,
            'product_uom': uom_id,
            'product_uos_qty': uos_id and uos_qty or False,
            'product_uos': uos_id or False,
            'location_id': source_location_id,
            'location_dest_id': destination_location_id,
            'company_id': production.company_id.id,
            'procure_method': prev_move and 'make_to_stock' or self._get_raw_material_procure_method(cr, uid, product, context=context), #Make_to_stock avoids creating procurement
            'raw_material_production_id': production.id,
            #this saves us a browse in create()
            'price_unit': product.standard_price,
            'origin': production.name,
            'warehouse_id': loc_obj.get_warehouse(cr, uid, production.location_src_id, context=context),
        }, context=context)

        if prev_move:
            context = dict(context)
            context['production_id'] = production.id
            prev_move = self._create_previous_move(cr, uid, move_id, product, prod_location_id, source_location_id, context=context)
            stock_move.action_confirm(cr, uid, [prev_move], context=context)
        return move_id


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
        for line in production.move_lines:
            new_consume_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.product_uom_qty
            }))

        return {'value': {'consume_lines': new_consume_lines}}
