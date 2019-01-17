# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    show_manual_lot_assign_button = fields.Boolean(
        compute='_show_manual_lot_assign_button')
    reserved_lots_available_qty = fields.Float(string='Available',
        compute='_reserved_lots_available_qty')
    old_lots_unused = fields.Boolean(compute='_reserved_lots_available_qty')

    @api.one
    def _show_manual_lot_assign_button(self):
        self.show_manual_lot_assign_button = \
            self.picking_id and \
            (
                self.picking_id.picking_type_code == 'outgoing' or
                (
                    self.picking_id.picking_type_code == 'internal' and
                    self.is_hoard_move
                )
            ) and \
            self.picking_id.state in ('assigned', 'partially_available')

    @api.one
    def _reserved_lots_available_qty(self):
        if self.picking_id and \
           self.picking_id.picking_type_code == 'internal' and \
           self.state in ('assigned', 'confirmed', 'partially_available', 'done') and \
           self.lot_ids:
            quant_ids = self.env['stock.quant'].search([
                ('lot_id', 'in', self.lot_ids.ids),
                ('location_id', 'child_of', self.location_id.id),
                ('product_id', '=', self.product_id.id),
                ('qty', '>', 0),
                '|',
                ('reservation_id', '=', False),
                ('reservation_id', '=', self.id)
            ])
            self.reserved_lots_available_qty = sum(quant_ids.mapped('qty'))

            # Check if any old lot is unused
            quant_ids = self.env['stock.quant'].search([
                ('lot_id', 'not in', self.lot_ids.ids),
                ('location_id', 'child_of', self.location_id.id),
                ('product_id', '=', self.product_id.id),
                ('qty', '>', 0),
                '|',
                ('reservation_id', '=', False),
                ('reservation_id', '=', self.id)
            ])
            self.old_lots_unused = (quant_ids and \
                min(quant_ids.mapped('lot_id.id')) < min(self.lot_ids.ids))

    @api.multi
    def action_manual_lot_assign_wizard(self):
        view = self.env.ref(
            'stock_move_manual_lot_assign.assign_manual_lots_form_view')

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.move.assign.manual.lot',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'context': self.env.context,
        }