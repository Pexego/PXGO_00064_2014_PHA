# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class PrestashopShop(models.Model):
    _inherit = "prestashop.shop"

    partner_categ_id = fields.Many2one("res.partner.category", "Category for partners")
    partner_pricelist_id = fields.Many2one("product.pricelist", "Pricelist")
