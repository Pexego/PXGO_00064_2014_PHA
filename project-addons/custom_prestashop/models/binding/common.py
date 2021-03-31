# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models


class PrestashopBinding(models.AbstractModel):
    _inherit = "prestashop.binding"

    _sql_constraints = [
        (
            "prestashop_uniq",
            "Check(1=1)",
            "A record with same ID already exists on PrestaShop.",
        ),
    ]
