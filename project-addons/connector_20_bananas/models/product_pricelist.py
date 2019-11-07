# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class ProductPricelist(models.Model):

    _inherit = "product.pricelist"

    custom_partner_pricelist_ids = fields.One2many(
        "product.pricelist.custom.partner", "orig_pricelist_id"
    )
    bananas_id = fields.Char(compute="_compute_bananas_id")
    bananas_synchronized = fields.Boolean()

    @api.multi
    def _compute_bananas_id(self):
        for pricelist in self:
            pricelist.bananas_id = pricelist.id

    def update_partner_pricelist(self, product):
        for custom_pricelist in self.custom_partner_pricelist_ids.filtered(
            "active"
        ):
            custom_pricelist.recompute_prices(product)

    def check_create_custom_pricelist(
        self, partner, commercial_discount=False, financial_discount=False
    ):
        self.ensure_one()
        custom_pricelist = self.custom_partner_pricelist_ids.filtered(
            lambda r: r.partner_id == partner and r.active
        )
        if not custom_pricelist:
            custom_pricelist = self.env[
                "product.pricelist.custom.partner"
            ].search(
                [
                    ("active", "=", False),
                    ("partner_id", "=", partner.id),
                    (
                        "commercial_financial_discount",
                        "=",
                        "{}-{}".format(commercial_discount, financial_discount),
                    ),
                ]
            )
            if custom_pricelist:
                custom_pricelist.write({"active": True})
        if not custom_pricelist:
            custom_pricelist = self.env[
                "product.pricelist.custom.partner"
            ].create(
                {
                    "partner_id": partner.id,
                    "orig_pricelist_id": self.id,
                    "commercial_financial_discount": "{}-{}".format(
                        commercial_discount, financial_discount
                    ),
                }
            )
        custom_pricelist.recompute_prices(
            commercial_discount=commercial_discount,
            financial_discount=financial_discount,
        )


class ProductPricelistItem(models.Model):

    _inherit = "product.pricelist.item"
    bananas_price = fields.Float(compute="_compute_bananas_price")

    @api.multi
    def _compute_bananas_price(self):
        for item in self:
            if item.product_id:
                item.bananas_price = item.price_version_id.pricelist_id.price_get(
                    item.product_id.id, 1
                )[
                    item.price_version_id.pricelist_id.id
                ]
            else:
                item.banans_price = 0

    @api.model
    def create(self, vals):
        res = super(ProductPricelistItem, self).create(vals)
        self.price_version_id.pricelist_id.update_partner_pricelist(
            self.product_id
        )
        return res

    @api.multi
    def write(self, vals):
        res = super(ProductPricelistItem, self).write(vals)
        for item in self:
            item.price_version_id.pricelist_id.update_partner_pricelist(
                item.product_id
            )
        return res

    @api.multi
    def unlink(self):
        for item in self:
            item.price_version_id.pricelist_id.update_partner_pricelist(
                item.product_id
            )
        return super(ProductPricelistItem, self).unlink()
