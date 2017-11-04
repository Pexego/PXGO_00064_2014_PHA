# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.one
    @api.constrains('state')
    def update_total_qty_in_production(self):
        self.product_id.update_qty_in_production()
