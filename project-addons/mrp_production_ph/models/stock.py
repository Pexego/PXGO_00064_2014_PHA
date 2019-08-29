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