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
        if self.lot_ids:
            wizard_id = self.env['stock.move.assign.manual.lot'].\
                with_context({'active_id': self.id, 'compute_only': True}).\
                create({})
            available_qty = 0
            for lot in self.lot_ids:
                wizard_line_ids = wizard_id.line_ids.\
                    filtered(lambda l: l.lot_id == lot)
                if wizard_line_ids:
                    available_qty += sum(wizard_line_ids.mapped('available_qty'))
            self.reserved_lots_available_qty = available_qty

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