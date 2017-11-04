# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.one
    @api.constrains('state', 'product_qty')
    def update_total_qty_in_production(self):
        self.product_id.product_tmpl_id.compute_detailed_stock()
        for material in self.move_lines:
            material.product_tmpl_id.compute_detailed_stock()
