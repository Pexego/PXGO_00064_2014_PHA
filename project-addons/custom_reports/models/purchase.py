# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    product_supplier_reference = fields.Char(compute='_get_supplier_reference')

    @api.one
    def _get_supplier_reference(self):
        if self.product_id.suppliers_pricelists:
            self.product_supplier_reference = self.product_id.\
                suppliers_pricelists.\
                filtered(lambda r: r.suppinfo_id.name == self.partner_id)[0].\
                suppinfo_id.product_name
