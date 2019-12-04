# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
import requests
from openerp.addons.connector.event import (
    on_record_create,
    on_record_unlink,
    on_record_write,
)
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Exporter

from ..backend import bananas
from ..unit.backend_adapter import GenericAdapter
from .utils import _get_exporter


@bananas
class PartnerPricelistExporter(Exporter):

    _model_name = ["product.pricelist.custom.partner"]

    def insert(self, partner_id, pricelist_id, mode):
        vals = {"codtarifa": pricelist_id, "codcliente": partner_id}
        return self.backend_adapter.insert(vals)

    def delete(self, vals):
        return self.backend_adapter.remove_vals(vals)


@bananas
class PartnerPricelistAdapter(GenericAdapter):
    _model_name = "product.pricelist.custom.partner"
    _bananas_model = "tarifasXclientes"
    _delete_id_in_url = False


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def export_partner_pricelist(session, model_name, record_id):
    partner_pricelist_exporter = _get_exporter(
        session,
        "product.pricelist.custom.partner",
        record_id,
        PartnerPricelistExporter,
    )
    partner = session.env[model_name].browse(record_id)
    return partner_pricelist_exporter.insert(
        partner.bananas_id, partner.get_bananas_pricelist().bananas_id, "insert"
    )


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def unlink_partner_pricelist(session, model_name, record_id):
    partner_pricelist_exporter = _get_exporter(
        session,
        "product.pricelist.custom.partner",
        record_id,
        PartnerPricelistExporter,
    )
    partner = session.env[model_name].browse(record_id)
    backend = partner_pricelist_exporter.backend_record
    url = "%s/%s/*/%s" % (
        backend.location,
        "tarifasXclientes",
        partner.bananas_id,
    )
    headers = {"apikey": backend.api_key, "Content-Type": "application/json"}
    result = requests.request("GET", url, headers=headers)
    records = result.json()["records"]
    if records:
        for record in records:
            partner_pricelist_exporter.delete(record)
    partner.check_custom_pricelist(
        partner.commercial_discount, partner.financial_discount
    )
    return


@bananas
class PricelistExporter(Exporter):

    _model_name = ["bananas.pricelist"]

    def insert(self, binding_id, mode):
        partner = self.env["res.partner"].browse(binding_id)
        pricelist = partner.get_bananas_pricelist()
        vals = {"codtarifa": pricelist.bananas_id}
        if pricelist._name == "product.pricelist.custom.partner":
            vals["descripcion"] = partner.name
        else:
            vals["descripcion"] = pricelist.name
        return self.backend_adapter.insert(vals)

    def delete(self, binding_id):
        partner = self.env["res.partner"].browse(binding_id)
        pricelist = partner.get_bananas_pricelist()
        return self.backend_adapter.remove(pricelist.id)


@bananas
class PricelistAdapter(GenericAdapter):
    _model_name = "bananas.pricelist"
    _bananas_model = "tarifas"


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def export_pricelist(session, model_name, record_id):
    pricelist_exporter = _get_exporter(
        session, "bananas.pricelist", record_id, PricelistExporter
    )
    return pricelist_exporter.insert(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def unlink_pricelist(session, model_name, record_id):
    pricelist_exporter = _get_exporter(
        session, "bananas.pricelist", record_id, PricelistExporter
    )
    return pricelist_exporter.delete(record_id)


@bananas
class CustomerRateExporter(Exporter):

    _model_name = ["product.pricelist.custom.partner.item"]

    def update(self, binding_id, mode):
        customer_rate = self.model.browse(binding_id)
        vals = {
            "codtarifa": customer_rate.pricelist_id.bananas_id,
            "referencia": customer_rate.product_id.id,
            "precio": customer_rate.price,
        }
        if mode == "insert":
            self.backend_adapter.insert(vals)
        else:
            self.backend_adapter.update(binding_id, vals)

    def delete(self, data):
        self.backend_adapter.remove_vals(data)


@bananas
class CustomerRateAdapter(GenericAdapter):
    _model_name = "product.pricelist.custom.partner.item"
    _bananas_model = "tarifasXarticulos"


@bananas
class CustomerRateExporter2(Exporter):

    _model_name = ["product.pricelist.item"]

    def update(self, binding_id, mode):
        customer_rate = self.model.browse(binding_id)
        vals = {
            "codtarifa": customer_rate.price_version_id.pricelist_id.bananas_id,
            "referencia": customer_rate.product_id.id,
            "precio": customer_rate.bananas_price,
        }
        if mode == "insert":
            self.backend_adapter.insert(vals)
        else:
            self.backend_adapter.update(binding_id, vals)

    def delete(self, data):
        self.backend_adapter.remove_vals(data)


@bananas
class CustomerRateAdapter2(GenericAdapter):
    _model_name = "product.pricelist.item"
    _bananas_model = "tarifasXarticulos"


@on_record_create(
    model_names=[
        "product.pricelist.custom.partner.item",
        "product.pricelist.item",
    ]
)
def delay_export_customer_rate_create(session, model_name, record_id, vals):
    export_customer_rate.delay(
        session, model_name, record_id, priority=20, eta=200
    )


@on_record_write(
    model_names=[
        "product.pricelist.custom.partner.item",
        "product.pricelist.item",
    ]
)
def delay_export_customer_rate_write(session, model_name, record_id, vals):
    update_customer_rate.delay(
        session, model_name, record_id, priority=20, eta=200
    )


@on_record_unlink(
    model_names=[
        "product.pricelist.custom.partner.item",
        "product.pricelist.item",
    ]
)
def delay_unlink_customer_rate(session, model_name, record_id):
    rate = session.env[model_name].browse(record_id)
    if model_name == "product.pricelist.custom.partner.item":
        data = {
            "codtarifa": rate.pricelist_id.bananas_id,
            "referencia": rate.product_id.id,
        }
    else:
        data = {
            "codtarifa": rate.price_version_id.pricelist_id.bananas_id,
            "referencia": rate.product_id.id,
        }
    unlink_customer_rate.delay(
        session, model_name, record_id, data=data, priority=1
    )


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def export_customer_rate(session, model_name, record_id):
    if model_name == "product.pricelist.custom.partner.item":
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter
        )
    else:
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter2
        )
    return customer_rate_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def update_customer_rate(session, model_name, record_id):
    if model_name == "product.pricelist.custom.partner.item":
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter
        )
    else:
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter2
        )
    return customer_rate_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def unlink_customer_rate(session, model_name, record_id, data):
    if model_name == "product.pricelist.custom.partner.item":
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter
        )
    else:
        customer_rate_exporter = _get_exporter(
            session, model_name, record_id, CustomerRateExporter2
        )
    return customer_rate_exporter.delete(data)
