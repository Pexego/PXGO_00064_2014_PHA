# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _


class ProductPricelistItem(models.Model):
    _inherit = 'product.pricelist.item'

    pricelist_id = fields.Many2one(related='price_version_id.pricelist_id',
                                   readonly=True)
    customer_price_to_third_parties = fields.Float(default=0)
