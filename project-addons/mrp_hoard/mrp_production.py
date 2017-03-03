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

    hoard_ids = fields.Many2many('stock.picking', string='hoard',
                                compute='_get_hoard_picking')
    hoard_len = fields.Integer('hoard len', compute='_get_hoard_len')
    return_operation_ids = fields.One2many('stock.move.return.operations',
                                           'production_id',
                                           'Return operations')
    accept_multiple_raw_material = fields.Boolean(
        compute='_get_accept_multiple_raw_material')

    @api.one
    @api.depends('routing_id.machinery_ids.accept_more_than_one_raw_material')
    def _get_accept_multiple_raw_material(self):
        self.accept_multiple_raw_material = any(self.mapped('routing_id.machinery_ids.accept_more_than_one_raw_material'))

    @api.one
    @api.depends('move_lines.move_orig_ids', 'move_lines2.move_orig_ids')
    def _get_hoard_len(self):
        pickings = self.env['stock.picking']
        pickings += self.mapped('move_lines.move_orig_ids.picking_id').sorted() \
            | self.mapped('move_lines2.move_orig_ids.picking_id').sorted()
        self.hoard_len = len(pickings)

    @api.one
    @api.depends('move_lines.move_orig_ids', 'move_lines2.move_orig_ids')
    def _get_hoard_picking(self):
        pickings = self.env['stock.picking']
        pickings += self.mapped('move_lines.move_orig_ids.picking_id').sorted() \
            | self.mapped('move_lines2.move_orig_ids.picking_id').sorted()
        self.hoard_ids = pickings or False

    @api.multi
    def get_hoard(self):
        action = self.env.ref('stock.action_picking_tree')
        if not action:
            return
        action = action.read()[0]
        if len(self.hoard_ids) > 1:
            action['domain'] = "[('id','in',[" + ','.join(map(str, self.hoard_ids.ids)) + "])]"
        else:
            res = self.env.ref('stock.view_picking_form')
            action['views'] = [(res.id, 'form')]
            action['res_id'] = self.hoard_ids.id
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
