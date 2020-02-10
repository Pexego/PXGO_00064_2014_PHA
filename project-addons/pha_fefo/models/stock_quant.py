# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class StockQuant(models.Model):

    _inherit = "stock.quant"
    date_in_system = fields.Date(related="lot_id.date_in_system", store=True)
    date_in = fields.Date(related="lot_id.date_in", store=True)

    @api.model
    def apply_removal_strategy(
        self, location, product, quantity, domain, removal_strategy
    ):
        if removal_strategy == "fefo_pha":
            order = "date_in_system, date_in,in_date, location_id, package_id, lot_id, id"
            return self._quants_get_order(
                location, product, quantity, domain, order
            )
        return super(StockQuant, self).apply_removal_strategy(
            location, product, quantity, domain, removal_strategy
        )
