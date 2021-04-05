# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
import logging
from openerp.addons.connector_prestashop.models.product_template.importer import (
    TemplateMapper,
    TemplateRecordImport,
)
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.backend_adapter import GenericAdapter
from openerp.addons.connector.unit.mapper import mapping, only_create

_logger = logging.getLogger(__name__)
try:
    from prestapyt import PrestaShopWebServiceError
except ImportError:
    _logger.debug("Can not `from prestapyt import PrestaShopWebServiceError`.")


@prestashop(replacing=TemplateMapper)
class CustomTemplateMapper(TemplateMapper):

    direct = []

    @only_create
    @mapping
    def odoo_id(self, record):
        """ Will bind the product to an existing one with the same code """
        product = self.env["product.template"].search(
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
                ).product_tmpl_id.id
            }

    @mapping
    def list_price(self, record):
        return {}

    @mapping
    def name(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(CustomTemplateMapper, self).name(record)
        return {}

    @mapping
    def date_add(self, record):
        return {}

    @mapping
    def date_upd(self, record):
        return {}

    @mapping
    def default_code(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(CustomTemplateMapper, self).default_code(record)
        return {}

    @mapping
    def description(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(CustomTemplateMapper, self).description(record)
        return {}

    @mapping
    def active(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return {"active": False}
        return {}

    @mapping
    def sale_ok(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(CustomTemplateMapper, self).sale_ok(record)
        return {}

    @mapping
    def purchase_ok(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(CustomTemplateMapper, self).purchase_ok(record)
        return {}

    @mapping
    def categ_id(self, record):
        return {}

    @mapping
    def categ_ids(self, record):
        return {}

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def company_id(self, record):
        return {}

    @mapping
    def ean13(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(CustomTemplateMapper, self).ean13(record)
        return {}

    @mapping
    def taxes_id(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(CustomTemplateMapper, self).taxes_id(record)

    @mapping
    def type(self, record):
        if self.odoo_id(record)['odoo_id'] == self.env.ref( "custom_prestashop.product_product_generic_prestasghop" ).product_tmpl_id.id:
            return {}
        if "-" in record["reference"] or re.match(
            "[0-9]{1}[Xx]{1}", record["reference"]
        ):
            return super(CustomTemplateMapper, self).type(record)
        return {}

    @mapping
    def procure_method(self, record):
        return {}

    @mapping
    def tags_to_text(self, record):
        return {}


@prestashop(replacing=TemplateRecordImport)
class TemplateRecordImportCustom(TemplateRecordImport):

    # def import_combinations(self):
    #     return

    def import_images(self, erp_id):
        return

    def import_supplierinfo(self, erp_id):
        return

    def _import_dependencies(self):
        record = self.prestashop_record
        reference = record["reference"]
        try:
            if "-" in reference:
                backend_adapter = self.unit_for(
                    GenericAdapter, "prestashop.product.template"
                )
                reference = re.sub("[0-9]{1}[Xx]{1}", "", reference)
                reference = reference.replace("(", "").replace(")", "")
                pack_products = reference.split("-")
                for prod_ref in pack_products:
                    product_ids = backend_adapter.search(
                        {"filter[reference]": prod_ref}
                    )
                    for prod_id in product_ids:
                        self._import_dependency(prod_id, "prestashop.product.template")
        except PrestaShopWebServiceError:
            pass

    def _has_to_skip(self):
        """ Return True if the import can be skipped """
        if self.prestashop_record.get("active") in ("0", 0):
            return True
