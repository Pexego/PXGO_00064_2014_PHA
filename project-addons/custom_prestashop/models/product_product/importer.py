# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
from openerp.addons.connector_prestashop.models.product_product.importer import (
    ProductCombinationMapper,
)
from openerp.addons.connector_prestashop.unit.backend_adapter import GenericAdapter
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector.unit.mapper import mapping, only_create


@prestashop(replacing=ProductCombinationMapper)
class ProductCombinationMapperCustom(ProductCombinationMapper):
    @only_create
    @mapping
    def odoo_id(self, record):
        product = self.env["product.product"].search(
            [("default_code", "=", record["reference"])], limit=1
        )
        if product:
            return {"odoo_id": product.id}
        else:
            if "-" in record["reference"] or re.match(
                "[0-9]{1}[Xx]{1}", record["reference"]
            ):
                # creamos los productos para los packs
                return {}
            return {
                "odoo_id": self.env.ref(
                    "custom_prestashop.product_product_generic_prestasghop"
                ).id
            }

    @mapping
    def combination_default(self, record):
        pass

    @mapping
    def product_tmpl_id(self, record):
        # if '-' in record['reference'] or re.match('[0-9]{1}[Xx]{1}', record['reference']):
        #     return super(ProductCombinationMapperCustom, self).product_tmpl_id(record)
        pass

    @mapping
    def from_main_template(self, record):
        # if '-' in record['reference'] or re.match('[0-9]{1}[Xx]{1}', record['reference']):
        #     return super(ProductCombinationMapperCustom, self).from_main_template(record)
        pass

    def main_template(self, record):
        # if '-' in record['reference'] or re.match('[0-9]{1}[Xx]{1}', record['reference']):
        #     return super(ProductCombinationMapperCustom, self).main_template(record)
        pass

    def get_main_template_id(self, record):
        # if '-' in record['reference'] or re.match('[0-9]{1}[Xx]{1}', record['reference']):
        #     return super(ProductCombinationMapperCustom, self).get_main_template_id(record)
        pass

    def get_main_template(self, record):
        # if '-' in record['reference'] or re.match('[0-9]{1}[Xx]{1}', record['reference']):
        #     return super(ProductCombinationMapperCustom, self).get_main_template(record)
        pass

    # def _get_option_value(self, record):
    #     pass

    @mapping
    def name(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            backend_adapter = self.unit_for(
                GenericAdapter, "prestashop.product.template"
            )
            template = backend_adapter.read(record["id_product"])
            return {
                "name": template["name"]["language"][0]["value"]
                + ": "
                + ", ".join([x.name for x in self._get_option_value(record)])
            }

    @mapping
    def attribute_value_ids(self, record):
        pass

    @mapping
    def main_template_id(self, record):
        pass

    def _template_code_exists(self, code):
        pass

    @mapping
    def default_code(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(ProductCombinationMapperCustom, self).default_code(record)

    @mapping
    def ean13(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(ProductCombinationMapperCustom, self).ean13(record)
        pass

    def _get_tax_ids(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(ProductCombinationMapperCustom, self)._get_tax_ids(record)

    @mapping
    def specific_price(self, record):
        pass

    @mapping
    def pack_line_ids(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).id:
            return {}
        pack_components = []
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            reference = record["reference"]
            if "(" in reference:
                new_ref = ""
                if "(" in reference:
                    new_ref = reference[: reference.index("(") - 2]
                    reference = reference[reference.index("(") - 2 :]
                while "(" in reference:
                    inicio = reference.index("(")
                    fin = reference.index(")")
                    new_ref += reference[: inicio - 2]
                    multiplicador = reference[inicio - 2 : inicio]
                    new_references = []
                    for subref in reference[inicio + 1 : fin].split("-"):
                        new_references.append("{}{}".format(multiplicador, subref))
                    new_ref += "-".join(new_references)
                    reference = reference[fin + 1 :]
                    if "(" not in reference:
                        new_ref += reference
                        reference = ""
                reference = new_ref
            backend_adapter = self.unit_for(
                GenericAdapter, "prestashop.product.template"
            )
            pack_components = [(5,)]
            # reference = re.sub('[0-9]{1}[Xx]{1}', '', reference)
            pack_products = reference.split("-")
            for prod_ref in pack_products:
                if prod_ref.startswith("F"):
                    quantity = 1
                else:
                    quantity = int(prod_ref[0])
                    prod_ref = prod_ref[2:]
                product_ids = backend_adapter.search({"filter[reference]": prod_ref})
                if product_ids:
                    product = self.binder_for("prestashop.product.template").to_odoo(
                        product_ids[0], unwrap=True
                    )
                    product = product.product_variant_ids[0]
                else:
                    prod_ids = self.env["product.product"].search(
                        [("default_code", "=", prod_ref)]
                    )
                    if not prod_ids:
                        raise Exception("product not found {}".format(prod_ref))
                    product = prod_ids[0]
                pack_components.append(
                    (0, 0, {"product_id": product.id, "quantity": quantity})
                )
        if pack_components:
            return {"pack_line_ids": pack_components}
