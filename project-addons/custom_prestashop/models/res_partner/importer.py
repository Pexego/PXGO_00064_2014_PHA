# -*- coding: utf-8 -*-
# © 2020 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from math import e
import re
from openerp.addons.connector_prestashop.connector import add_checkpoint
from openerp.addons.connector_prestashop.models.res_partner.importer import (
    PartnerImportMapper,
    ResPartnerRecordImport,
    AddressImportMapper,
    AddressImporter,
)

from openerp.addons.connector_prestashop.unit.backend_adapter import PrestaShopCRUDAdapter
from openerp.addons.connector.unit.mapper import mapping, only_create
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector_prestashop.unit.mapper import backend_to_m2o


def _formatString(text):
    """Formats the string into a fixed length ASCII (iso-8859-1) record.

    Note:
        'Todos los campos alfanuméricos y alfabéticos se presentarán
        alineados a la izquierda y rellenos de blancos por la derecha,
        en mayúsculas sin caracteres especiales, y sin vocales acentuadas.
        Para los caracteres específicos del idioma se utilizará la
        codificación ISO-8859-1. De esta forma la letra “Ñ” tendrá el
        valor ASCII 209 (Hex. D1) y la “Ç” (cedilla mayúscula) el valor
        ASCII 199 (Hex. C7).'
    """
    # Replace accents and convert to upper
    from unidecode import unidecode
    text = unicode(text).upper()
    text = ''.join([unidecode(x) if x not in (u'Ñ', u'Ç') else x
                    for x in text])
    text = re.sub(
        ur"[^A-Z0-9\s\.,-_&'´\\:;/\(\)ÑÇ\"]", '', text, re.UNICODE | re.X)
    return text


def _formatFiscalName(text):
    name = re.sub(
        ur"[^a-zA-Z0-9\sáÁéÉíÍóÓúÚñÑçÇäÄëËïÏüÜöÖ"
        ur"àÀèÈìÌòÒùÙâÂêÊîÎôÔûÛ\.,-_&'´\\:;:/]", '', text,
        re.UNICODE | re.X)
    name = re.sub(r'\s{2,}', ' ', name, re.UNICODE | re.X)
    return _formatString(name)


@prestashop(replacing=ResPartnerRecordImport)
class ResPartnerRecordImportCustom(ResPartnerRecordImport):

    def _import_dependencies(self):
        return


@prestashop(replacing=PartnerImportMapper)
class PartnerImportMapperCustom(PartnerImportMapper):
    direct = [
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        ('email', 'email'),
        ('newsletter', 'newsletter'),
        ('company', 'company'),
        ('active', 'active'),
        ('note', 'comment'),
        (backend_to_m2o('id_shop_group'), 'shop_group_id'),
        (backend_to_m2o('id_shop'), 'shop_id'),
    ]

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
        name = name.upper()
        return {"name": _formatFiscalName(name)}

    @only_create
    @mapping
    def odoo_id(self, record):
        backend_adapter = self.unit_for(
            PrestaShopCRUDAdapter, 'prestashop.address')
        address_ids = backend_adapter.search(filters={'filter[id_customer]': '%d' % (int(record['id']))})
        vat_number = None
        for address_id in address_ids:
            addresses_data = backend_adapter.read(address_id)

            if addresses_data["vat_number"]:
                vat_number = addresses_data["vat_number"].replace(".", "").replace(" ", "")
            # TODO move to custom localization module
            elif not addresses_data["vat_number"] and addresses_data.get("dni"):
                vat_number = (
                    addresses_data["dni"].replace(".", "").replace(" ", "").replace("-", "")
                )
            if vat_number:
                if len(vat_number) == 8:
                    vat_number = '0' + vat_number
                # TODO: move to custom module
                regexp = re.compile("^[a-zA-Z]{2}")
                if not regexp.match(vat_number):
                    vat_number = "ES" + vat_number
                break
        if vat_number:
            partner = self.env["res.partner"].search(
                [("vat", "=ilike", vat_number)], limit=1
            )

        else:
            partner = self.env["res.partner"].search(
                [("email", "=ilike", record["email"])], limit=1
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
            "send_invoice_by_email": True,
        }

    @mapping
    def groups(self, record):
        result = {}
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

    direct = [
        ('address1', 'street'),
        ('address2', 'street2'),
        ('city', 'city'),
        ('other', 'comment'),
        ('postcode', 'zip'),
        ('date_add', 'date_add'),
        ('date_upd', 'date_upd'),
        (backend_to_m2o('id_customer'), 'prestashop_partner_id'),
    ]

    @mapping
    def phone(self, record):
        vals = {}
        if record.get('phone'):
            vals['phone'] = record.get('phone')
        if record.get('phone_mobile'):
            vals['mobile'] = record.get('phone_mobile')
        return vals

    @mapping
    def lang(self, record):
        parent = self.binder_for('prestashop.res.partner').to_odoo(
            record['id_customer'], unwrap=True)
        return {'lang': parent.lang}

    @mapping
    def name(self, record):
        name = ""
        if record["lastname"]:
            name += record["lastname"]
        if record["firstname"]:
            if name:
                name += ", "
            name += record["firstname"]
        name = name.upper()
        return {"name": _formatFiscalName(name)}

    @mapping
    def groups(self, record):
        result = {}
        category = self.binder_for("prestashop.res.partner").to_odoo(
            record["id_customer"]).shop_id.partner_categ_id
        if category:
            result["category_id"] = [(6, 0, [category.id])]
        return result

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

    @mapping
    def state_id(self, record):
        if record.get("id_country") and record.get("postcode"):
            binder = self.binder_for("prestashop.res.country")
            country = binder.to_odoo(record["id_country"], unwrap=True)
            city_zip = self.env["res.better.zip"].search(
                [
                    ("name", "=", record.get("postcode")),
                    ("country_id", "=", country.id),
                ]
            )
            if not city_zip:
                # Portugal
                city_zip = self.env["res.better.zip"].search(
                    [
                        ("name", "=", record.get("postcode").replace(' ', '-')),
                        ("country_id", "=", country.id),
                    ]
                )
                if not city_zip:
                    # Portugal 2
                    city_zip = self.env["res.better.zip"].search(
                        [
                            ("name", "=", record.get("postcode")[:4] + '-' + record.get("postcode")[4:]),
                            ("country_id", "=", country.id),
                        ]
                    )
            if city_zip:
                res = {"state_id": city_zip[0].state_id.id}
                if len(city_zip) == 1:
                    res['zip_id'] = city_zip.id
                return res


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
            if self._check_vat(vat_number.upper()):
                binding.parent_id.write({"vat": vat_number.upper()})
            else:
                add_checkpoint(
                    self.session,
                    "res.partner",
                    binding.parent_id.id,
                    self.backend_record.id,
                )
        else:
            if not binding.parent_id.vat:
                binding.parent_id.write(
                    {"sii_simplified_invoice": True, "simplified_invoice": True}
                )
        if binding.phone and not binding.parent_id.phone:
            binding.parent_id.phone = binding.phone
        elif not binding.phone and not binding.parent_id.phone:
            binding.odoo_id.phone = '.'
            binding.parent_id.phone = '.'
        if binding.mobile and not binding.parent_id.mobile:
            binding.parent_id.mobile = binding.mobile
        elif not binding.mobile and not binding.parent_id.mobile:
            binding.odoo_id.mobile = '.'
            binding.parent_id.mobile = '.'
        if binding.zip_id and not binding.parent_id.zip_id:
            binding.parent_id.zip_id = binding.zip_id
        if binding.parent_id.email and not binding.email:
            binding.odoo_id.email = binding.parent_id.email
        binding.parent_id.is_company = False
