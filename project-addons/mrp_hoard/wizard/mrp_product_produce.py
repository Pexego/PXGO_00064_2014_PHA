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
import openerp.addons.decimal_precision as dp


class MrpProductProduceLine(models.TransientModel):

    _inherit = 'mrp.product.produce.line'
    operation_id = fields.Many2one('stock.move.return.operations', 'Operation')


class MrpProductProduceReturnLine(models.TransientModel):
    _name = 'mrp.product.produce.return.line'

    product_id = fields.Many2one('product.product', 'Product')
    product_qty = fields.Float('Quantity (in default UoM)',
                               digits=dp.get_precision(
                                   'Product Unit of Measure'))
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    location_id = fields.Many2one('stock.location', 'Dest location')
    produce_id = fields.Many2one('mrp.product.produce')
    operation_id = fields.Many2one('stock.move.return.operations', 'Operation')


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    _defaults = {
        'mode': lambda *x: 'consume',
    }

    return_lines = fields.One2many('mrp.product.produce.return.line',
                                   'produce_id', 'Products To return')

    def on_change_qty(self, cr, uid, ids, product_qty, consume_lines,
                      context=None):
        prod_obj = self.pool.get("mrp.production")
        production = prod_obj.browse(cr, uid, context['active_id'],
                                     context=context)
        new_consume_lines = []
        return_lines = []
        for line in production.return_operation_ids:
            new_consume_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.hoard_served_qty - line.hoard_returned_qty
                - line.qty_scrapped,
                'lot_id': line.lot_id,
                'operation_id': line.id,
            }))
            return_lines.append((0, 0, {
                'product_id': line.product_id.id,
                'product_qty': line.hoard_returned_qty,
                'lot_id': line.lot_id,
                'operation_id': line.id,
                'location_id': line.location_id.id
            }))
        return {'value': {'consume_lines': new_consume_lines,
                          'return_lines': return_lines}}

    @api.model
    def get_operations(self, move):
        stop = False
        move_aux = move
        while not stop:
            if move_aux.split_from:
                move_aux = move_aux.split_from
            else:
                stop = True
        return move_aux.return_operation_ids

    @api.multi
    def do_produce(self):
        """
            Se actualizan las operaciones con los datos finales.
            Si se han añadido lineas se crean opearciones.
            Cuando la cantidad servida - cantidad(de movimiento) > devuelta
            solo se resta a la servida. Si no hay movimiento siempre se resta.
        """
        scrap_location = self.env['stock.location'].search(
            [('scrap_location', '=', True)])
        if not scrap_location:
            raise exceptions.Warning(_('Location not found'),
                                     _('Scrap location not found.')
                                     )
        scrap_location = scrap_location[0]
        if self.mode in ('consume_produce', 'only_produce'):
            return super(
                MrpProductProduce,
                self.with_context(no_return_operations=True)).do_produce()
        originals = self.env['stock.move']
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        main_production_move = False
        for produce_product in production.move_created_ids:
                if produce_product.product_id.id == production.product_id.id:
                    main_production_move = produce_product.id
        for move in production.move_lines:
            move.do_unreserve()
        lines = []
        for consume_line in self.consume_lines:
            '''Se guarda en 1 diccionario cantidad consumida(de acopio),
               sobreconsumida(consumida despues de acopio), devuelta,
               estropeada'''
            line_dict = {
                'product_id': consume_line.product_id,
                'lot_id': consume_line.lot_id,
                'operation_id': consume_line.operation_id,
                'returned_qty': 0.0,
            }
            if consume_line.operation_id:
                line_dict.update({
                    'consumed_qty': consume_line.operation_id.qty >=
                    consume_line.product_qty and consume_line.product_qty or
                    consume_line.operation_id.qty,
                    'over_consumed': consume_line.operation_id.qty <
                    consume_line.product_qty and consume_line.product_qty -
                    consume_line.operation_id.qty or 0.0,
                    'make_return': consume_line.operation_id.qty >=
                    consume_line.product_qty,
                })
            else:
                line_dict.update({
                    'consumed_qty': 0.0,
                    'over_consumed': consume_line.product_qty,
                    'make_return': False
                })
            lines.append(line_dict)
        for return_line in self.return_lines:
            for line in lines:
                if line['lot_id'] == return_line.lot_id:
                    line['returned_qty'] = return_line.product_qty
                    if line.get('make_return', False):
                        line['return_location_id'] = return_line.location_id
        for line in lines:
            if not line['operation_id']:
                self.env['stock.move.return.operations'].create(
                    {'production_id': production.id,
                     'lot_id': line['lot_id'].id,
                     'hoard_served_qty': line['consumed_qty'] +
                     line['over_consumed'] + line['returned_qty'],
                     'hoardreturned_qty': line['returned_qty']})
            else:
                if line['operation_id'].hoard_served_qty != \
                        line['consumed_qty'] + line['over_consumed'] + \
                        line['returned_qty']:
                    line['operation_id'].hoard_served_qty = \
                        line['consumed_qty'] + line['over_consumed'] + \
                        line['returned_qty']
                if line['operation_id'].hoard_returned_qty != \
                        line['returned_qty']:
                    line['operation_id'].hoard_returned_qty = \
                        line['returned_qty']
            if line['operation_id'].move_id:
                move = line['operation_id'].move_id
                if move.state != 'done':
                    move.do_unreserve()
                    move.product_uom_qty = line['consumed_qty']
                    move.restrict_lot_id = line['lot_id'].id
                    move.consumed_for = main_production_move
                    move.with_context(no_return_operations=True).action_assign()
                    move.action_done()
                else:
                    new_move = move.copy({
                        'product_uom_qty': line['consumed_qty'],
                        'restrict_lot_id': line['lot_id'].id,
                        'return_production_move': True,
                        'consumed_for': main_production_move,
                        })
                    new_move.action_confirm()
                    new_move.action_assign()
                    new_move.action_done()
            else:
                move = self.env['stock.move'].search(
                    [('product_id', '=', line['product_id'].id),
                     ('raw_material_production_id', '=', production.id),
                     ('return_production_move', '=', False)])
            if line['over_consumed']:
                over_move = move.copy({
                    'product_uom_qty': line['over_consumed'],
                    'restrict_lot_id': line['lot_id'].id,
                    'location_id': production.location_src_id.id,
                    'return_production_move': True,
                        'consumed_for': main_production_move,
                    })
                over_move.action_confirm()
                over_move.action_assign()
                over_move.action_done()
            if line['make_return'] and line['returned_qty'] > 0:
                return_dict = {
                    'product_uom_qty': line['returned_qty'],
                    'restrict_lot_id': line['lot_id'].id,
                    'return_production_move': True,
                    'consumed_for': main_production_move,
                }
                if move.original_move:
                    if move.original_move.state != 'done':
                        move.original_move.do_unreserve()
                        move.original_move.product_uom_qty += line['returned_qty']
                        return_dict['location_dest_id'] = move.original_move.location_id.id
                        return_dict['move_dest_id'] = move.original_move.id
                    else:
                        return_dict['location_dest_id'] = move.original_move.location_dest_id.id
                else:
                    return_dict['location_dest_id'] = line['return_location_id'].id
                return_move = move.copy(return_dict)
                return_move.action_confirm()
                return_move.action_assign()
                return_move.action_done()
                if move.original_move:
                    move.original_move.action_assign()
            if line['operation_id'].qty_scrapped > 0:
                scrap_move = move.copy({
                    'product_uom_qty': line['operation_id'].qty_scrapped,
                    'restrict_lot_id': line['lot_id'].id,
                    'location_dest_id': scrap_location.id,
                    'return_production_move': True,
                    'consumed_for': main_production_move,
                    })
                scrap_move.action_confirm()
                scrap_move.action_assign()
                scrap_move.action_done()
        return {}
