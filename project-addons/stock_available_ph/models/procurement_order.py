# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.model
    def _procure_orderpoint_confirm(self, use_new_cursor=False,
                                    company_id=False):
        return super(ProcurementOrder,
                     self.with_context(disable_notify_changes=True)).\
            _procure_orderpoint_confirm(use_new_cursor, company_id)

    @api.model
    def _product_virtual_get(self, order_point):
        order_point.product_id.product_tmpl_id.compute_detailed_stock()
        return order_point.product_id.virtual_conservative
