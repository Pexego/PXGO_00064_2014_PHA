# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class PrestashopProductCombination(models.Model):
    _inherit = "prestashop.product.combination"

    main_template_id = fields.Many2one(
        required=False,
    )

    # _sql_constraints = [
    #     ('prestashop_product_combination_prestashop_erp_uniq', 'Check(1=1)',
    #      'A record with same ID already exists on PrestaShop.'),
    # ]

    def init(self, cr):
        cr.execute(
            "alter table prestashop_product_combination "
            "drop constraint if exists prestashop_product_combination_prestashop_erp_uniq"
        )
        return True
