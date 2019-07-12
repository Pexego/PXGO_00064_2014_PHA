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
class WhiteListExporter(Exporter):

    _model_name = ['bananas.whitelist']

    def update(self, binding_id, mode):
        customer_rate = self.model.browse(binding_id)
        vals = {
            "codcliente": customer_rate.partner_id.id,
            "codproducto": customer_rate.product_id.id,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, data):
        return self.backend_adapter.remove_vals(data)


@bananas
class WhiteListAdapter(GenericAdapter):
    _model_name = 'bananas.whitelist'
    _bananas_model = 'listablanca'


@on_record_create(model_names='bananas.whitelist')
def delay_export_whitelist_create(session, model_name, record_id, vals):
    export_whitelist.delay(
        session, model_name, record_id, priority=20, eta=110)


@on_record_write(model_names='bananas.whitelist')
def delay_export_whitelist_write(session, model_name, record_id, vals):
    whitelist = session.env[model_name].browse(record_id)
    if vals['price'] and vals['price'] != whitelist.last_sync_price:
        vals['last_sync_price'] = vals['price']
        update_whitelist.delay(
            session, model_name, record_id, priority=20, eta=120)


@on_record_unlink(model_names='bananas.whitelist')
def delay_unlink_whitelist(session, model_name, record_id):
        rate = session.env[model_name].browse(record_id)
        data = {
            'codtarifa': rate.partner_id.id,
            'referencia': rate.product_id.id,
        }
        unlink_whitelist.delay(
            session, model_name, record_id, data=data, priority=1)

@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_whitelist(session, model_name, record_id):
    whitelist_exporter = _get_exporter(
        session, 'bananas.pricelist.customer', record_id, WhiteListExporter)
    return whitelist_exporter.insert(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_whitelist(session, model_name, record_id):
    whitelist_exporter = _get_exporter(
        session, 'bananas.pricelist.customer', record_id, WhiteListExporter)
    return whitelist_exporter.delete(record_id)
