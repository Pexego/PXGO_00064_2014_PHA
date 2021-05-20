# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models


class PrestashopProductTemplate(models.Model):
    _inherit = "prestashop.product.template"

    def init(self, cr):
        cr.execute(
            "alter table prestashop_product_template "
            "drop constraint if exists prestashop_product_template_prestashop_erp_uniq"
        )
        return True
