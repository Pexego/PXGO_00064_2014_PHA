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


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    hoard_id = fields.Many2one('stock.picking', string='hoard',
                                compute='_get_hoard_picking')
    hoard_len = fields.Integer('hoard len', compute='_get_hoard_len')
    return_operation_ids = fields.One2many('stock.move.return.operations',
                                           'production_id',
                                           'Return operations')

    @api.one
    @api.depends('hoard_id')
    def _get_hoard_len(self):
        self.hoard_len = len(self.hoard_id)

    @api.one
    @api.depends('move_lines.move_orig_ids', 'move_lines2.move_orig_ids')
    def _get_hoard_picking(self):
        pickings = self.env['stock.picking']
        pickings += self.mapped('move_lines.move_orig_ids.picking_id').sorted() \
            | self.mapped('move_lines2.move_orig_ids.picking_id').sorted()
        self.hoard_id = pickings and pickings[0] or False

    @api.multi
    def get_hoard(self):
        action = self.env.ref('stock.action_picking_tree')
        if not action:
            return
        action = action.read()[0]
        res = self.env.ref('stock.view_picking_form')
        action['views'] = [(res.id, 'form')]
        action['res_id'] = self.hoard_id
        action['context'] = False
        return action

    def action_cancel(self, cr, uid, ids, context=None):
        """ Cancels the production order and related stock moves.
        @return: True
        """
        if context is None:
            context = {}
        move_obj = self.pool.get('stock.move')
        proc_obj = self.pool.get('procurement.order')
        for production in self.browse(cr, uid, ids, context=context):
            if production.move_created_ids:
                move_obj.action_cancel(cr, uid, [x.id for x in production.move_created_ids])
            moves = move_obj.search(cr, uid, [('move_dest_id', 'in', [x.id for x in production.move_lines])], context=context)
            if moves:
                move_ids = []
                for move in move_obj.browse(cr, uid, moves, context):
                    if move.state not in ('cancel', 'done'):
                        move_ids.append(move.id)
                move_obj.action_cancel(cr, uid, move_ids, context=context)
            move_obj.action_cancel(cr, uid, [x.id for x in production.move_lines])
        self.write(cr, uid, ids, {'state': 'cancel'})
        # Put related procurements in exception
        proc_obj = self.pool.get("procurement.order")
        procs = proc_obj.search(cr, uid, [('production_id', 'in', ids)],
                                context=context)
        if procs:
            proc_obj.write(cr, uid, procs, {'state': 'exception'},
                           context=context)
        return True


class MrpProductProduce(models.TransientModel):
    _inherit = "mrp.product.produce"

    def on_change_qty(self, cr, uid, ids, product_qty, consume_lines,
                      context=None):
        prod_obj = self.pool.get("mrp.production")
        uom_obj = self.pool.get("product.uom")
        production = prod_obj.browse(cr, uid, context['active_id'],
                                     context=context)
        new_consume_lines = []
        for move in production.move_lines:
            for line in move.return_operation_ids:
                new_consume_lines.append((0, 0, {
                    'product_id': line.product_id.id,
                    'product_qty': line.qty - line.returned_qty -
                    line.qty_scrapped,
                    'lot_id': line.lot_id
                }))

        return {'value': {'consume_lines': new_consume_lines}}

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
        res = super(MrpProductProduce, self.with_context(no_return_operations=True)).do_produce()
        originals = self.env['stock.move']
        production = self.env['mrp.production'].browse(self.env.context.get('active_id', False))
        for move in production.move_lines:
            operations = self.get_operations(move)
            for op in operations:
                if op.qty_scrapped > 0:
                    scrap_location_id = self.env['stock.location'].search(
                        [('scrap_location', '=', True)])
                    if not scrap_location_id:
                        raise exceptions.Warning(_('Location not found'),
                                                 _('Scrap location not found.')
                                                 )
                    default_val = {
                        'product_uom_qty': op.qty_scrapped,
                        'served_qty': 0,
                        'returned_qty': 0,
                        'qty_scrapped': 0,
                        'restrict_lot_id': op.lot_id.id,
                        'scrapped': True,
                        'location_dest_id': scrap_location_id[0].id,
                    }
                    move.do_unreserve()
                    move.product_uom_qty -= op.qty_scrapped
                    move.with_context(no_return_operations=True).action_assign()
                    new_move = move.copy(default_val)
                    new_move.action_confirm()
                    new_move.with_context(no_return_operations=True).action_assign()
                    new_move.action_done()
            dest_location = move.raw_material_production_id.location_src_id.id
            if move.original_move:
                # Si se ha consumido cuarentena, la cantidad no consumida se
                # devuelve al movimiento del flujo original.
                if move.original_move.state != 'done':
                    dest_location = move.original_move.location_id.id
                    move.original_move.do_unreserve()
                    move.original_move.product_uom_qty += operations[0].returned_qty
                    originals += move.original_move
                else:
                    dest_location = move.original_move.location_dest_id.id
            move.location_dest_id = dest_location
            if len(operations) == 1:
                move.restrict_lot_id = operations[0].lot_id.id
            elif len(operations) > 1:
                move.restrict_lot_id = operations[0].lot_id.id
                move.do_unreserve()
                move.product_uom_qty = operations[0].returned_qty
                for op in operations:
                    if op.id == operations[0].id:
                        continue
                    default_val = {
                        'product_uom_qty': op.returned_qty,
                        'restrict_lot_id': op.lot_id.id,
                        'location_dest_id': dest_location,
                    }
                    new_move = move.copy(default_val)
                    new_move.action_confirm()
                    new_move.with_context(no_return_operations=True).action_assign()
                    new_move.action_done()
                move.with_context(no_return_operations=True).action_assign()
            move.action_done()

        originals.action_assign()
        return res
