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
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import ValidationError, Warning as UserError
from openerp.tools.float_utils import float_round


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
    total_qty = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'))


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    _defaults = {
        'mode': lambda *x: 'consume',
    }

    return_lines = fields.One2many('mrp.product.produce.return.line',
                                   'produce_id', 'Products To return')

    @api.onchange('return_lines')
    def onchange_return_lines(self):
        for line in self.return_lines:
            consume_line = line.produce_id.consume_lines.filtered(
                lambda r: r.product_id == line.product_id and
                r.lot_id == line.lot_id)
            if line.product_qty > line.total_qty:
                raise ValidationError(_('.'))
            if consume_line:
                consume_line.product_qty = line.total_qty - line.product_qty

    @api.multi
    def _calculate_consumptions(self, production):
        bom_point = production.bom_id
        # get components and workcenter_lines from BoM structure
        factor = self.env['product.uom']._compute_qty(
            production.product_uom.id,
            production.final_qty,
            bom_point.product_uom.id)
        # product_lines, workcenter_lines
        return self.env['mrp.bom']._bom_explode(
            bom_point, production.product_id, factor / bom_point.product_qty,
            None, routing_id=production.routing_id.id)[0]

    @api.model
    def _get_source_location(self, product_id, lot_id):
        production = self.env['mrp.production'].browse(
            self._context['active_id'])
        quants = production.mapped('move_lines.reserved_quant_ids').filtered(
            lambda r: r.product_id.id == product_id and r.lot_id.id == lot_id)
        if quants and quants[0].reservation_id.move_orig_ids:
            return quants[0].reservation_id.move_orig_ids[0].\
                linked_move_operation_ids[0].operation_id.location_id.id

    def on_change_qty(self, cr, uid, ids, product_qty, consume_lines,
                      context=None):
        prod_obj = self.pool.get("mrp.production")
        production = prod_obj.browse(cr, uid, context['active_id'],
                                     context=context)
        new_consume_lines = []
        return_lines = []
        calculated_consumption = self._calculate_consumptions(
            cr, uid, ids, production, context)
        product_lines = {}
        for line in calculated_consumption:
            product = self.pool.get('product.product').browse(
                cr, uid, line['product_id'], context)
            product_lines[line['product_id']] = float_round(
                line['product_qty'] *
                (1 + product.categ_id.decrease_percentage / 100),
                precision_rounding=product.uom_id.rounding)
        all_bom_products = [x['product_id'] for x in calculated_consumption]
        added_moves = [x for x in production.mapped('move_lines') if
                       x.product_id.id not in all_bom_products]
        for move in added_moves:
            product_lines[move.product_id.id] = move.product_uom_qty
        quant_ids = production.mapped('move_lines.reserved_quant_ids.id')
        product_lot_qty = self.pool.get('stock.quant').read_group(
            cr, uid, [('id', 'in', quant_ids)],
            ['product_id', 'lot_id', 'qty'], ['product_id', 'lot_id'],
            context=context, orderby='product_id', lazy=False)
        for product in product_lines.keys():
            product_qty = product_lines[product]
            current_product_lots = [x for x in product_lot_qty if
                                    x['product_id'][0] == product]
            for line in current_product_lots:
                if product_qty >= line['qty']:
                    line_qty = line['qty']
                    product_qty -= line['qty']
                    return_lines.append((0, 0, {
                        'product_id': line['product_id'][0],
                        'lot_id': line['lot_id'][0],
                        'product_qty': 0,
                        'total_qty': line['qty'],
                        'location_id': self._get_source_location(
                            cr, uid, line['product_id'][0], line['lot_id'][0],
                            context)
                    }))
                else:
                    rest = line['qty'] - product_qty
                    line_qty = line['qty'] - rest
                    return_lines.append((0, 0, {
                        'product_id': line['product_id'][0],
                        'lot_id': line['lot_id'][0],
                        'product_qty': rest,
                        'total_qty': line['qty'],
                        'location_id': self._get_source_location(
                            cr, uid, line['product_id'][0], line['lot_id'][0],
                            context)
                    }))
                    product_qty = 0
                new_consume_lines.append((0, 0, {
                    'product_id': line['product_id'][0],
                    'lot_id': line['lot_id'][0],
                    'product_qty': line_qty,
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
        scrap_location = self.env['stock.location'].search(
            [('scrap_location', '=', True)])
        if not scrap_location:
            raise UserError(
                _('Location not found'),
                _('Scrap location not found.'))
        scrap_location = scrap_location[0]
        if self.mode in ('consume_produce', 'only_produce'):
            return super(
                MrpProductProduce,
                self.with_context(no_return_operations=True)).do_produce()
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        main_production_move = False
        for produce_product in production.move_created_ids + \
                production.move_created_ids2:
            if produce_product.product_id.id == production.product_id.id:
                main_production_move = produce_product.id
        # Nunca se consumirá una cantidad mayor a la de los movimientos
        # ya existentes, por lo que simplemente tenemos que preocuparnos
        # por las devoluciones.
        for consume in self.consume_lines:
            remaining_qty = consume['product_qty']
            for raw_material_line in production.move_lines:
                if raw_material_line.state in ('done', 'cancel'):
                    continue
                if remaining_qty <= 0:
                    break
                if consume.product_id.id != raw_material_line.product_id.id:
                    continue
                consumed_qty = min(
                    remaining_qty, raw_material_line.product_qty)
                raw_material_line.action_consume(
                    consumed_qty, raw_material_line.location_id.id,
                    restrict_lot_id=consume.lot_id.id,
                    consumed_for=main_production_move)
                remaining_qty -= consumed_qty
        for return_line in self.return_lines.filtered(lambda r: r.product_qty > 0):
            for raw_material_line in production.move_lines:
                if raw_material_line.state in ('done', 'cancel'):
                    continue
                if return_line.product_id.id != raw_material_line.product_id.id:
                    continue
                raw_material_line.do_unreserve()
                old_location = raw_material_line.location_dest_id.id
                raw_material_line.write({
                    'return_production_move': True,
                    'location_dest_id': return_line.location_id.id
                })
                raw_material_line.action_assign()
                new_split_id = raw_material_line.action_consume(
                    return_line.product_qty,
                    restrict_lot_id=return_line.lot_id.id,
                    consumed_for=main_production_move)
                if new_split_id:
                    new_split = self.env['stock.move'].browse(new_split_id)
                    new_split.write({
                        'return_production_move': False,
                        'location_dest_id': old_location
                    })
        if production.move_lines:
            raise ValidationError(
                'Error al finalizar. Quedan movimientos sin finalizar.')
        production.move_created_ids.action_cancel()
        production.signal_workflow('button_produce_done')
        return {}
