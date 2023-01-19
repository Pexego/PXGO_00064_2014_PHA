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
                "[0-9]{1,2}[Xx]{1}", record["reference"]
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

    @only_create
    @mapping
    def name(self, record):
        if self.odoo_id(record).get('odoo_id') == self.env.\
                ref( "custom_prestashop.product_product_generic_prestasghop" ).\
                id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1,2}[Xx]{1}", record["reference"]
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

    @only_create
    @mapping
    def default_code(self, record):
        if self.odoo_id(record).get('odoo_id') == self.env.\
                ref( "custom_prestashop.product_product_generic_prestasghop" ).id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1,2}[Xx]{1}", record["reference"]
        ):
            return super(ProductCombinationMapperCustom, self).\
                default_code(record)

    @only_create
    @mapping
    def ean13(self, record):
        if self.odoo_id(record).get('odoo_id') == self.env.\
                ref( "custom_prestashop.product_product_generic_prestasghop" ).id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1,2}[Xx]{1}", record["reference"]
        ):
            return super(ProductCombinationMapperCustom, self).ean13(record)
        pass

    def _get_tax_ids(self, record):
        if self.odoo_id(record).get('odoo_id') == self.env.\
                ref( "custom_prestashop.product_product_generic_prestasghop" ).\
                id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1,2}[Xx]{1}", record["reference"]
        ):
            return super(ProductCombinationMapperCustom, self)._get_tax_ids(record)

    @mapping
    def specific_price(self, record):
        pass

    @mapping
    def pack_line_ids(self, record):
        if self.odoo_id(record).get('odoo_id') == self.env.\
                ref( "custom_prestashop.product_product_generic_prestasghop" ).id:
            return {}
        pack_components = []
        if "-" in record["reference"] or re.match(
            "[0-9]{1,2}[Xx]{1}", record["reference"]
        ):
            reference = record["reference"]
            # Expands occurrences of type 13x(FXXXX-FYYYY-FZZZZ)
            # with or without multiplier
            group_pattern = r'(?:\d{1,2}[Xx]{1}){0,1}\(.*?\)'
            multiplier_pattern = r'\d{1,2}[Xx]{1}(?=\()'
            reference_pattern = r'(?<=[\(-]).*?(?=[\)-])'
            for group_match in re.findall(group_pattern, reference):
                aux_ref = ''
                multiplier_match = re.search(multiplier_pattern,
                                             group_match)
                if multiplier_match:
                    multiplier = multiplier_match.group()
                else:
                    multiplier = ''
                for ref in re.finditer(reference_pattern, group_match):
                    aux_ref += ('-' if aux_ref > '' else '') + \
                               multiplier + ref.group()
                reference = reference.replace(group_match, aux_ref)

            template_backend_adapter = self.unit_for(
                GenericAdapter, "prestashop.product.template"
            )
            combination_backend_adapter = self.unit_for(
                GenericAdapter, "prestashop.product.combination"
            )

            pack_components = [(5,)]
            pack_products = reference.split('-')
            multiplier_pattern = r'^\d{1,2}(?=[Xx]{1})'
            for prod_ref in pack_products:
                multiplier_match = re.search(multiplier_pattern, prod_ref)
                if multiplier_match:
                    qty_str = multiplier_match.group()
                    quantity = int(qty_str)
                    prod_ref = prod_ref[len(qty_str) + 1:]
                else:
                    quantity = 1

                template_ids = template_backend_adapter.\
                    search({"filter[reference]": prod_ref, "filter[active]": 1})
                if template_ids:
                    product_ids = combination_backend_adapter.\
                        search({"filter[reference]": prod_ref,
                                "filter[id_product]": template_ids[0]})
                    product = self.binder_for("prestashop.product.combination").\
                        to_odoo(product_ids[0], unwrap=True)
                    product = product
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
