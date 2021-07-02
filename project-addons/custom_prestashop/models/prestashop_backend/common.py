# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models, api


class PrestashopBackend(models.Model):
    _inherit = "prestashop.backend"

    sale_channel_id = fields.Many2one(
        "sale.channel", string="Sale channel", required=True
    )
    salesperson_id = fields.Many2one("res.users")
    gift_product_ids = fields.One2many('prestashop.backend.gift.product', 'backend_id')

    @api.multi
    def import_customers_since(self):
        return True


class PrestashopBackendGiftProduct(models.Model):

    _name = 'prestashop.backend.gift.product'

    product_id = fields.Many2one('product.product', 'product', required=True)
    quantity = fields.Float(default=1.0)
    backend_id = fields.Many2one('prestashop.backend')
