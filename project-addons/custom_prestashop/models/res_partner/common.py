# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.multi
    def onchange_partner_id(self, part):
        res = super(SaleOrder, self).onchange_partner_id(part)
        if "value" in res and "payment_mode_id" in res["value"]:
            if self._context.get("payment_method", False):
                payment_method = self.env["payment.method"].browse(
                    self._context.get("payment_method", False)
                )
                if payment_method.payment_mode_id:
                    res["value"]["payment_mode_id"] = payment_method.payment_mode_id.id
        return res
