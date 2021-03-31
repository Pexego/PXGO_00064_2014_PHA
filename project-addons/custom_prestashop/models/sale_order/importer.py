# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

import logging
from openerp.addons.connector_prestashop.models.sale_order.importer import (
    SaleOrderMapper,
    SaleOrderLineMapper,
    SaleOrderImport,
)
from openerp.addons.connector_prestashop.unit.backend_adapter import GenericAdapter
from openerp.addons.connector.unit.mapper import mapping
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.mapper import backend_to_m2o
import re

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Can not `from prestapyt import PrestaShopWebServiceError`.")


@prestashop(replacing=SaleOrderMapper)
class SaleOrderMapperCustom(SaleOrderMapper):
    @mapping
    def sale_channel_id(self, record):
        return {"sale_channel_id": self.backend_record.sale_channel_id.id}

    @mapping
    def client_order_ref(self, record):
        return {"client_order_ref": record["reference"]}

    @mapping
    def name(self, record):
        return {}

    @mapping
    def fiscal_position_id(self, record):
        partner_id = self.partner_id(record)["partner_id"]
        partner = self.env["res.partner"].browse(partner_id)
        if partner.property_account_position:
            return {"fiscal_position_id": partner.property_account_position.id}
        order_lines = record.get("associations").get("order_rows").get("order_row")
        if isinstance(order_lines, dict):
            order_lines = [order_lines]
        line_taxes = []
        sale_line_adapter = self.unit_for(GenericAdapter, "prestashop.sale.order.line")
        for line in order_lines:
            line_data = sale_line_adapter.read(line["id"])
            prestashop_tax_id = (
                line_data.get("associations").get("taxes").get("tax").get("id")
            )
            if prestashop_tax_id not in line_taxes:
                line_taxes.append(prestashop_tax_id)

        fiscal_positions = self.env["account.fiscal.position"]
        for tax_id in line_taxes:
            matched_fiscal_position = self.env["account.fiscal.position"].search(
                [("prestashop_tax_ids", "ilike", tax_id)]
            )
            fiscal_positions += matched_fiscal_position.filtered(
                lambda r: tax_id in r.prestashop_tax_ids.split(",")
            )
        if len(fiscal_positions) != 1:
            raise Exception(
                "Error al importar posicion fiscal para los impuestos {}".format(
                    line_taxes
                )
            )
        return {"fiscal_position_id": fiscal_positions.id}

    @mapping
    def pricelist_id(self, record):
        binder = self.binder_for("prestashop.shop")
        shop = binder.to_odoo(record["id_shop"])
        if shop.partner_pricelist_id:
            return {"pricelist_id": shop.partner_pricelist_id.id}


# @prestashop(replacing=SaleOrderLineMapper)
# class SaleOrderLineMapperCustom(SaleOrderLineMapper):

#     @mapping
#     def product_id(self, record):
#         backend_adapter = self.unit_for(
#             GenericAdapter, 'prestashop.product.template')
#         product_rec = backend_adapter.read(record['product_id'])
#         product = self.env['product.product'].search([('default_code', '=', product_rec['reference'])])
#         if not product:
#             product = self.env.ref('custom_prestashop.product_product_generic_prestasghop')
#         if product is None:
#             return self.tax_id(record)
#         return {'product_id': product.id}


@prestashop(replacing=SaleOrderImport)
class SaleOrderImportCustom(SaleOrderImport):
    def _import_dependencies(self):
        record = self.prestashop_record
        self._import_dependency(record["id_customer"], "prestashop.res.partner")
        self._import_dependency(record["id_address_invoice"], "prestashop.address")
        self._import_dependency(record["id_address_delivery"], "prestashop.address")

        if record["id_carrier"] != "0":
            self._import_dependency(record["id_carrier"], "prestashop.delivery.carrier")

        orders = (
            record["associations"]
            .get("order_rows", {})
            .get(self.backend_record.get_version_ps_key("order_row"), [])
        )
        if isinstance(orders, dict):
            orders = [orders]
        backend_adapter = self.unit_for(GenericAdapter, "prestashop.product.template")
        for order in orders:
            reference = backend_adapter.read(order["product_id"])["reference"]
            try:
                if "-" in reference:
                    reference = re.sub("[0-9]{1}[Xx]{1}", "", reference)
                    reference = reference.replace("(", "").replace(")", "")
                    pack_products = reference.split("-")
                    for prod_ref in pack_products:
                        product_ids = backend_adapter.search(
                            {"filter[reference]": prod_ref}
                        )
                        for prod_id in product_ids:
                            self._import_dependency(
                                prod_id, "prestashop.product.template"
                            )
                else:
                    self._import_dependency(
                        order["product_id"], "prestashop.product.template"
                    )
            except PrestaShopWebServiceError:
                pass

    def _after_import(self, binding):
        binding.odoo_id.expand_packs()
        return super(SaleOrderImportCustom, self)._after_import(binding)
