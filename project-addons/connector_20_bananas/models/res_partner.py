# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import api, fields, models


class ResPartner(models.Model):

    _inherit = "res.partner"

    bananas_id = fields.Integer()
    bananas_synchronized = fields.Boolean("Synchronized with 20 bananas")
    has_delivery_address = fields.Boolean(
        compute="_compute_has_delivery_address"
    )
    partner_pricelist_exported = fields.Boolean()

    def _compute_has_delivery_address(self):
        for partner in self:
            if (
                partner.is_company
                and partner.child_ids
                and partner.child_ids.filtered(lambda r: r.type == "delivery")
            ):
                partner.has_delivery_address = True

    def create_bananas_id(self):
        return self.env["ir.sequence"].next_by_id(
            self.env.ref("connector_20_bananas.sequence_partner_bananas_id").id
        )

    @api.model
    def create(self, vals):
        if vals.get("bananas_synchronized"):
            vals["bananas_id"] = self.create_bananas_id()
        partner = super(ResPartner, self).create(vals)
        if (
            partner.parent_id
            and partner.type == "delivery"
            and partner.parent_id.bananas_synchronized
        ):
            partner.bananas_synchronized = True
        return partner

    @api.multi
    def write(self, vals):
        for partner in self:
            if vals.get("bananas_synchronized"):
                partner.write({"bananas_id": self.create_bananas_id()})
            if (
                vals.get("parent_id")
                and vals.get("type", partner.type) == "delivery"
                and partner.parent_id.bananas_synchronized
                and not vals.get(
                    "bananas_synchronized", partner.bananas_synchronized
                )
            ):
                vals["bananas_synchronized"] = True
            elif (
                vals.get("bananas_synchronized")
                and partner.is_company
                and partner.child_ids
                and partner.child_ids.filtered(lambda r: r.type == "delivery")
            ):
                childs = partner.child_ids.filtered(
                    lambda r: r.type == "delivery"
                )
                for child in childs:
                    child.write({"bananas_synchronized": True})
            if (
                "bananas_synchronized" in vals
                and not vals["bananas_synchronized"]
                and partner.is_company
                and partner.child_ids
                and partner.child_ids.filtered(lambda r: r.type == "delivery")
            ):
                childs = partner.child_ids.filtered(
                    lambda r: r.type == "delivery"
                )
                for child in childs:
                    child.write({"bananas_synchronized": False})
        res = super(ResPartner, self).write(vals)
        return res

    @api.multi
    def check_custom_pricelist(self, commercial_discount, financial_discount):
        self.ensure_one()
        if (
            commercial_discount
            or financial_discount
            and self.property_product_pricelist
        ):
            self.property_product_pricelist.check_create_custom_pricelist(
                self, commercial_discount, financial_discount
            )

    def get_bananas_pricelist(self):
        partner_pricelist = self.property_product_pricelist
        custom_pricelist = partner_pricelist.custom_partner_pricelist_ids.filtered(
            lambda r: r.partner_id == self and r.active
        )
        return custom_pricelist or partner_pricelist

    def get_bananas_pricelist_items(self):
        pricelist = self.get_bananas_pricelist()
        if pricelist._name == "product.pricelist.custom.partner":
            return pricelist.pricelist_items
        else:
            return pricelist.version_id.items_id.filtered("product_id")
