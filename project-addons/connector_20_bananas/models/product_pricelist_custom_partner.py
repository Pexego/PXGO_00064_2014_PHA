# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class ProductPricelistCustomPartner(models.Model):

    _name = "product.pricelist.custom.partner"

    partner_id = fields.Many2one("res.partner")
    orig_pricelist_id = fields.Many2one("product.pricelist")
    bananas_id = fields.Char()
    bananas_synchronized = fields.Boolean()
    pricelist_items = fields.One2many(
        "product.pricelist.custom.partner.item", "pricelist_id"
    )
    active = fields.Boolean(default=True)
    commercial_financial_discount = fields.Char()

    @api.model
    def create(self, vals):
        vals["bananas_id"] = self.env["ir.sequence"].next_by_id(
            self.env.ref(
                "connector_20_bananas.sequence_partner_custom_pricelist_bananas_id"
            ).id
        )
        return super(ProductPricelistCustomPartner, self).create(vals)

    def recompute_prices(
        self, product=False, commercial_discount=False, financial_discount=False
    ):
        if not commercial_discount:
            commercial_discount = self.partner_id.commercial_discount
        if not financial_discount:
            financial_discount = self.partner_id.financial_discount
        updated_products = self.env["product.product"]
        for orig_item in self.orig_pricelist_id.mapped("version_id.items_id"):
            if product and orig_item.product_id != product:
                continue
            custom_item = self.pricelist_items.filtered(
                lambda r: r.product_id == orig_item.product_id
            )
            price = self.orig_pricelist_id.price_get(
                orig_item.product_id.id, 1
            )[self.orig_pricelist_id.id]
            item_price = (
                price
                * (1 - (commercial_discount or 0.0) / 100.0)
                * (1 - (financial_discount or 0.0) / 100.0)
            )
            if not custom_item:
                custom_item = self.env[
                    "product.pricelist.custom.partner.item"
                ].create(
                    {
                        "pricelist_id": self.id,
                        "product_id": orig_item.product_id.id,
                        "price": item_price,
                    }
                )
            else:
                if custom_item.price != item_price:
                    custom_item.price = item_price
            if not product:
                updated_products += custom_item.product_id
        if not product:
            removed_items = self.pricelist_items.filtered(
                lambda r: r.product_id not in updated_products
            )
            for item in removed_items:
                asdasd
            removed_items.unlink()


class ProductPricelistCustomPartnerIten(models.Model):

    _name = "product.pricelist.custom.partner.item"

    pricelist_id = fields.Many2one("product.pricelist.custom.partner")
    product_id = fields.Many2one("product.product")
    price = fields.Float()
    bananas_price = fields.Float(related="price")
