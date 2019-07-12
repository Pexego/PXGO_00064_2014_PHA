# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector.queue.job import job
from .utils import _get_exporter
from ..backend import bananas
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter
from openerp.addons.connector.event import on_record_create, on_record_write, \
    on_record_unlink


@bananas
class PartnerPricelistExporter(Exporter):

    _model_name = ['bananas.pricelist.customer']

    def insert(self, binding_id, mode):
        vals = {
            'codtarifa': binding_id,
            'codcliente': binding_id
        }
        return self.backend_adapter.insert(vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@bananas
class PartnerPricelistAdapter(GenericAdapter):
    _model_name = 'bananas.pricelist.customer'
    _bananas_model = 'tarifasXclientes'
    _delete_id_in_url = True


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_partner_pricelist(session, model_name, record_id):
    partner_pricelist_exporter = _get_exporter(
        session, 'bananas.pricelist.customer', record_id, PartnerPricelistExporter)
    return partner_pricelist_exporter.insert(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_partner_pricelist(session, model_name, record_id):
    partner_pricelist_exporter = _get_exporter(
        session, 'bananas.pricelist.customer', record_id, PartnerPricelistExporter)
    return partner_pricelist_exporter.delete(record_id)


@bananas
class PricelistExporter(Exporter):

    _model_name = ['bananas.pricelist']

    def insert(self, binding_id, mode):
        partner = self.env['res.partner'].browse(binding_id)
        vals = {
            'codtarifa': binding_id,
            'descripcion': 'Tarifa %s' % partner.name,
        }
        return self.backend_adapter.insert(vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@bananas
class PricelistAdapter(GenericAdapter):
    _model_name = 'bananas.pricelist'
    _bananas_model = 'tarifas'


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_pricelist(session, model_name, record_id):
    pricelist_exporter = _get_exporter(
        session, 'bananas.pricelist', record_id, PricelistExporter)
    return pricelist_exporter.insert(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_pricelist(session, model_name, record_id):
    pricelist_exporter = _get_exporter(
        session, 'bananas.pricelist', record_id, PricelistExporter)
    return pricelist_exporter.delete(record_id)


@bananas
class CustomerRateExporter(Exporter):

    _model_name = ['bananas.customer.rate']

    def update(self, binding_id, mode):
        customer_rate = self.model.browse(binding_id)
        vals = {
            "codtarifa": customer_rate.partner_id.id,
            "referencia": customer_rate.product_id.id,
            "precio": customer_rate.last_sync_price,
        }
        if mode == "insert":
            self.backend_adapter.insert(vals)
            self.backend_adapter.insert_whitelist({
                'codcliente': vals['codtarifa'],
                'codproducto': vals['referencia']
            })
        else:
            self.backend_adapter.update(binding_id, vals)

    def delete(self, data):
        self.backend_adapter.remove_vals(data)
        self.backend_adapter.remove_whitelist({
            'codcliente': data['codtarifa'],
            'codproducto': data['referencia']
        })


@bananas
class CustomerRateAdapter(GenericAdapter):
    _model_name = 'bananas.customer.rate'
    _bananas_model = 'tarifasXarticulos'


@on_record_create(model_names='bananas.customer.rate')
def delay_export_customer_rate_create(session, model_name, record_id, vals):
    export_customer_rate.delay(
        session, model_name, record_id, priority=20, eta=110)


@on_record_write(model_names='bananas.customer.rate')
def delay_export_customer_rate_write(session, model_name, record_id, vals):
    customer_rate = session.env[model_name].browse(record_id)
    if vals['price'] and vals['price'] != customer_rate.last_sync_price:
        vals['last_sync_price'] = vals['price']
        update_customer_rate.delay(
            session, model_name, record_id, priority=20, eta=120)


@on_record_unlink(model_names='bananas.customer.rate')
def delay_unlink_customer_rate(session, model_name, record_id):
        rate = session.env[model_name].browse(record_id)
        data = {
            'codtarifa': rate.partner_id.id,
            'referencia': rate.product_id.id,
        }
        unlink_customer_rate.delay(
            session, model_name, record_id, data=data, priority=1)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_customer_rate(session, model_name, record_id):
    customer_rate_exporter = _get_exporter(
        session, model_name, record_id, CustomerRateExporter)
    return customer_rate_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_customer_rate(session, model_name, record_id):
    customer_rate_exporter = _get_exporter(
        session, model_name, record_id, CustomerRateExporter)
    return customer_rate_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_customer_rate(session, model_name, record_id, data):
    customer_rate_exporter = _get_exporter(
        session, model_name, record_id, CustomerRateExporter)
    return customer_rate_exporter.delete(data)
