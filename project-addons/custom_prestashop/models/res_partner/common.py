# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    @api.onchange("payment_method_id")
    def onchange_payment_method_id_set_payment_term(self):
        res = super(SaleOrder, self).onchange_payment_method_id_set_payment_term()
        if self.payment_method_id and self.payment_method_id.payment_mode_id:
            self.payment_mode_id = self.payment_method_id.payment_mode_id.id
        return res

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
