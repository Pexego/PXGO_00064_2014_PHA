# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector.event import on_record_create, on_record_write, \
    on_record_unlink
from openerp.addons.connector.queue.job import job
from .utils import _get_exporter
from ..backend import bananas
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter


@bananas
class ProductExporter(Exporter):

    _model_name = ['product.product']

    def update(self, binding_id, mode):
        product = self.model.browse(binding_id)
        vals = {
            "referencia": str(product.id),
            "nombre": product.name,
            "unidad": product.container_id.name,
            "unidadbulto": 'caja',
            "unidadesxbulto": product.box_elements,
            "familia": product.line.name,
            "subfamilia": product.subline.name,
            "vendounidad": 1,
            "vendobulto": 1,
            "descripcion": product.description_sale or '',
            "foto": product.external_image_url,
            'precio': 9999.99  # La app siempre muestra el precio mas bajo.
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@bananas
class ProductAdapter(GenericAdapter):
    _model_name = 'product.product'
    _bananas_model = 'articulos'


@on_record_create(model_names='product.product')
def delay_export_product_create(session, model_name, record_id, vals):
    product = session.env[model_name].browse(record_id)
    up_fields = ["name" "container_id", "box_elements",
                 "line", "subline", "description_sale"]

    if vals.get("bananas_synchronized", False) and \
            vals.get('active', product.active):
        export_product.delay(session, model_name, record_id, priority=1,
                             eta=60)
    elif vals.get("active", False) and \
            vals.get('bananas_synchronized', False) and \
            product.bananas_synchronized:
        export_product.delay(session, model_name, record_id, priority=1,
                             eta=60)
    elif product.bananas_synchronized:
        for field in up_fields:
            if field in vals:
                update_product.delay(
                    session, model_name, record_id, priority=5, eta=120)
                break


@on_record_write(model_names='product.product')
def delay_export_product_write(session, model_name, record_id, vals):
    product = session.env[model_name].browse(record_id)
    up_fields = ["name" "container_id", "box_elements",
                 "line", "subline", "description_sale"]
    if vals.get("bananas_synchronized", False) and \
            vals.get('active', product.active) and not product.bananas_synchronized:
        export_product.delay(session, model_name, record_id,
                             priority=1, eta=60)

    elif vals.get("active", False) and \
            vals.get('bananas_synchronized', False) and \
            product.bananas_synchronized:
        update_product.delay(session, model_name, record_id,
                             priority=1, eta=60)

    elif "bananas_synchronized" in vals and not vals["bananas_synchronized"]:
        unlink_product.delay(session, model_name, record_id,
                             priority=1, eta=60)

    elif product.bananas_synchronized and "active" in vals and not \
            vals["active"]:
        unlink_product.delay(session, model_name, record_id,
                             priority=1, eta=60)

    elif product.bananas_synchronized:
        for field in up_fields:
            if field in vals:
                update_product.delay(
                    session, model_name, record_id, priority=2, eta=120)
                break


@on_record_unlink(model_names='product.product')
def delay_unlink_product(session, model_name, record_id):
    product = session.env[model_name].browse(record_id)
    if product.bananas_synchronized:
        unlink_product.delay(session, model_name, record_id, eta=60)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_product(session, model_name, record_id):
    product_exporter = _get_exporter(session, model_name, record_id,
                                     ProductExporter)
    return product_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_product(session, model_name, record_id):
    product_exporter = _get_exporter(session, model_name, record_id,
                                     ProductExporter)
    return product_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_product(session, model_name, record_id):
    product_exporter = _get_exporter(session, model_name, record_id,
                                     ProductExporter)
    return product_exporter.delete(record_id)
