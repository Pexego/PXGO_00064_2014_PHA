# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    theorical_uom_qty = fields.Float(compute='_compute_theorical_uom_qty',
                                     string='Theorical qty.')

    @api.one
    def _compute_theorical_uom_qty(self):
        qty = 0
        pr = self.raw_material_production_id
        if pr:
            bl = pr.bom_id.bom_line_ids.filtered(
                lambda bl: bl.product_id == self.product_id)
            if bl:
                qty = bl.product_qty * pr.product_qty
        self.theorical_uom_qty = qty


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    production_state = fields.Selection([('draft', 'New'), ('cancel', 'Cancelled'),
        ('confirmed', 'Awaiting Raw Materials'), ('ready', 'Ready to Produce'),
        ('in_production', 'Production Started'), ('qty_set', 'Final quantity set'),
        ('released', 'Released'), ('done', 'Done'), ('n/a', '')],
                                        compute='_production_state')

    @api.one
    def _production_state(self):
        if self.lot_id.production_id:
            self.production_state = self.lot_id.production_id.state
        else:
            self.production_state = 'n/a'