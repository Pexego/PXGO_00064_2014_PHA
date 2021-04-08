# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import re
from openerp.addons.connector_prestashop.connector import add_checkpoint
from openerp.addons.connector_prestashop.models.res_partner.importer import (
    PartnerImportMapper,
    AddressImportMapper,
    AddressImporter,
)
from openerp.addons.connector.unit.mapper import mapping, only_create
from openerp.addons.connector_prestashop.backend import prestashop


@prestashop(replacing=PartnerImportMapper)
class PartnerImportMapperCustom(PartnerImportMapper):
    @mapping
    def user_id(self, record):
        return {"user_id": self.backend_record.salesperson_id.id}

    @mapping
    def is_company(self, record):
        # This is sad because we _have_ to have a company partner if we want to
        # store multiple adresses... but... well... we have customers who want
        # to be billed at home and be delivered at work... (...)...
        return {"is_company": False}

    @mapping
    def name(self, record):
        name = ""
        if record["lastname"]:
            name += record["lastname"]
        if record["firstname"]:
            if name:
                name += ", "
            name += record["firstname"]
        return {"name": name}

    @only_create
    @mapping
    def odoo_id(self, record):
        partner = self.env["res.partner"].search(
            [("email", "=", record["email"])], limit=1
        )
        if partner:
            return {"odoo_id": partner.id}
        else:
            {"pre_customer": True}

    @mapping
    def custom_mails(self, record):
        return {
            "invoice_claims_mail": record.get("email"),
            "sales_mail": record.get("email"),
            "email_to_send_invoice": record.get("email"),
        }

    @mapping
    def groups(self, record):
        groups = (
            record.get("associations", {})
            .get("groups", {})
            .get(self.backend_record.get_version_ps_key("group"), [])
        )
        if not isinstance(groups, list):
            groups = [groups]
        model_name = "prestashop.res.partner.category"
        partner_category_bindings = self.env[model_name].browse()
        binder = self.binder_for(model_name)
        for group in groups:
            partner_category_bindings |= binder.to_odoo(group["id"])
        result = {"group_ids": [(6, 0, partner_category_bindings.ids)]}
        category = (
            self.binder_for("prestashop.shop")
            .to_odoo(record["id_shop"])
            .partner_categ_id
        )
        if category:
            result["category_id"] = [(6, 0, [category.id])]
        return result

    @mapping
    def pricelist_id(self, record):
        pricelist = (
            self.binder_for("prestashop.shop")
            .to_odoo(record["id_shop"])
            .partner_pricelist_id
        )
        if pricelist:
            return {"property_product_pricelist": pricelist.id}
        return {}


@prestashop(replacing=AddressImportMapper)
class AddressImportMapperCustom(AddressImportMapper):
    @mapping
    def name(self, record):
        name = ""
        if record["lastname"]:
            name += record["lastname"]
        if record["firstname"]:
            if name:
                name += ", "
            name += record["firstname"]
        return {"name": name}

    @mapping
    def parent_id(self, record):
        parent = self.binder_for("prestashop.res.partner").to_odoo(
            record["id_customer"], unwrap=True
        )
        # if record['vat_number']:
        #     vat_number = record['vat_number'].replace('.', '').replace(' ', '')
        #     # TODO: move to custom module
        #     regexp = re.compile('^[a-zA-Z]{2}')
        #     if not regexp.match(vat_number):
        #         vat_number = 'ES' + vat_number
        #     if self._check_vat(vat_number):
        #         parent.write({'vat': vat_number})
        #     else:
        #         add_checkpoint(
        #             self.session,
        #             'res.partner',
        #             parent.id,
        #             self.backend_record.id
        #         )
        return {"parent_id": parent.id}

    # TODO move to custom localization module
    @mapping
    def dni(self, record):
        parent = self.binder_for("prestashop.res.partner").to_odoo(
            record["id_customer"], unwrap=True
        )
        # if not record['vat_number'] and record.get('dni'):
        #     vat_number = record['dni'].replace('.', '').replace(
        #         ' ', '').replace('-', '')
        #     regexp = re.compile('^[a-zA-Z]{2}')
        #     if not regexp.match(vat_number):
        #         vat_number = 'ES' + vat_number
        #     if self._check_vat(vat_number):
        #         parent.write({'vat': vat_number})
        #     else:
        #         add_checkpoint(
        #             self.session,
        #             'res.partner',
        #             parent.id,
        #             self.backend_record.id
        #         )
        return {"parent_id": parent.id}


@prestashop(replacing=AddressImporter)
class AddressImporterCustom(AddressImporter):
    def _after_import(self, binding):
        record = self.prestashop_record
        vat_number = None
        if record["vat_number"]:
            vat_number = record["vat_number"].replace(".", "").replace(" ", "")
        # TODO move to custom localization module
        elif not record["vat_number"] and record.get("dni"):
            vat_number = (
                record["dni"].replace(".", "").replace(" ", "").replace("-", "")
            )
        if vat_number:
            # TODO: move to custom module
            regexp = re.compile("^[a-zA-Z]{2}")
            if not regexp.match(vat_number):
                vat_number = "ES" + vat_number
            if self._check_vat(vat_number):
                binding.parent_id.write({"vat": vat_number})
            else:
                add_checkpoint(
                    self.session,
                    "res.partner",
                    binding.parent_id.id,
                    self.backend_record.id,
                )
        else:
            binding.parent_id.write(
                {"sii_simplified_invoice": True, "simplified_invoice": True}
            )
