# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector.event import on_record_create, on_record_write, \
    on_record_unlink
from openerp.addons.connector.queue.job import job
from .utils import _get_exporter
from .pricelist_events import export_partner_pricelist, export_pricelist, unlink_partner_pricelist, unlink_pricelist
from ..backend import bananas
from openerp.addons.connector.unit.synchronizer import Exporter
from ..unit.backend_adapter import GenericAdapter
from openerp.exceptions import Warning


@bananas
class PartnerExporter(Exporter):

    _model_name = ['res.partner']

    def update(self, binding_id, mode):
        partner = self.model.browse(binding_id)
        if not partner.user_id:
            raise Warning('Comercial no encontrado para el cliente %s' % partner.name)
        if not partner.mobile:
            raise Warning('movil no encontrado para el cliente %s' % partner.name)
        vals = {
            "nombrecliente": partner.name,
            "codcliente": str(partner.id),
            "codcomercial": 'PG5A0',#partner.user_id.id,
            "cif": partner.vat or "",
            "direccion": partner.street or "",
            "ciudad": partner.city or "",
            "cp": partner.zip,
            "codpais": partner.country_id and partner.country_id.code or
            "",
            "email": partner.email or "",
            "telefono": partner.mobile,
        }
        if mode == "insert":
            return self.backend_adapter.insert(vals)
        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        return self.backend_adapter.remove(binding_id)


@bananas
class PartnerAdapter(GenericAdapter):
    _model_name = 'res.partner'
    _bananas_model = 'clientes'


@on_record_create(model_names='res.partner')
def delay_export_partner_create(session, model_name, record_id, vals):
    partner = session.env[model_name].browse(record_id)
    up_fields = ["name" "vat", "city", "street", "zip",
                 "country_id", 'ref', 'user_id', "email", "phone", "mobile",
                 "bananas_synchronized"]

    if vals.get("bananas_synchronized", False) and \
            vals.get('active', partner.active):
        session.env['bananas.customer.rate'].calculate(partner=partner)
        export_partner.delay(session, model_name, record_id, priority=1)
        export_pricelist.delay(
            session, model_name, record_id, priority=2, eta=60)
        export_partner_pricelist.delay(
            session, model_name, record_id, priority=3, eta=80)
    elif vals.get("active", False) and \
            vals.get('bananas_synchronized', False) and \
            partner.bananas_synchronized:
        session.env['bananas.customer.rate'].calculate(partner=partner)
        export_partner.delay(session, model_name, record_id, priority=1,
                             eta=60)
        export_pricelist.delay(
            session, model_name, record_id, priority=2, eta=60)
        export_partner_pricelist.delay(
            session, model_name, record_id, priority=3, eta=80)
    elif partner.bananas_synchronized:
        for field in up_fields:
            if field in vals:
                update_partner.delay(
                    session, model_name, record_id, priority=5, eta=120)
                break


@on_record_write(model_names='res.partner')
def delay_export_partner_write(session, model_name, record_id, vals):
    partner = session.env[model_name].browse(record_id)
    up_fields = ["name", "vat", "city", "street", "zip",
                 "country_id", 'ref', 'user_id', "email", "phone", "mobile",
                 "bananas_synchronized"]
    if vals.get("bananas_synchronized", False) and \
            vals.get('active', partner.active):
        session.env['bananas.customer.rate'].calculate(partner=partner)
        export_partner.delay(session, model_name, record_id, priority=1)
        export_pricelist.delay(
            session, model_name, record_id, priority=2, eta=60)
        export_partner_pricelist.delay(
            session, model_name, record_id, priority=3, eta=80)

    elif vals.get("active", False) and \
            vals.get('bananas_synchronized', False) and \
            partner.bananas_synchronized:
        session.env['bananas.customer.rate'].calculate(partner=partner)
        export_partner.delay(session, model_name, record_id, priority=1)
        export_pricelist.delay(
            session, model_name, record_id, priority=2, eta=60)
        export_partner_pricelist.delay(
            session, model_name, record_id, priority=3, eta=80)
    elif "bananas_synchronized" in vals and not vals["bananas_synchronized"]:
        unlink_partner_pricelist.delay(
            session, model_name, record_id, priority=1)
        unlink_pricelist.delay(
            session, model_name, record_id, priority=2, eta=60)
        unlink_partner.delay(
            session, model_name, record_id, priority=3, eta=60)

    elif partner.bananas_synchronized and "active" in vals and not \
            vals["active"]:
        unlink_partner_pricelist.delay(
            session, model_name, record_id, priority=1)
        unlink_pricelist.delay(
            session, model_name, record_id, priority=2, eta=60)
        unlink_partner.delay(
            session, model_name, record_id, priority=3, eta=60)

    elif partner.bananas_synchronized:
        for field in up_fields:
            if field in vals:
                update_partner.delay(
                    session, model_name, record_id, priority=2, eta=120)
                break


@on_record_unlink(model_names='res.partner')
def delay_unlink_partner(session, model_name, record_id):
    partner = session.env[model_name].browse(record_id)
    if partner.bananas_synchronized:
        unlink_partner_pricelist.delay(
            session, model_name, record_id, priority=1)
        unlink_pricelist.delay(
            session, model_name, record_id, priority=2, eta=60)
        unlink_partner.delay(
            session, model_name, record_id, priority=3, eta=60)


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def export_partner(session, model_name, record_id):
    partner = session.env[model_name].browse(record_id)
    session.env['bananas.customer.rate'].calculate(partner=partner)
    partner_exporter = _get_exporter(session, model_name, record_id,
                                     PartnerExporter)
    return partner_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def update_partner(session, model_name, record_id):
    partner_exporter = _get_exporter(session, model_name, record_id,
                                     PartnerExporter)
    return partner_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60,
                    5: 50 * 60})
def unlink_partner(session, model_name, record_id):
    partner = session.env[model_name].browse(record_id)
    session.env['bananas.customer.rate'].remove(partner=partner)
    partner_exporter = _get_exporter(session, model_name, record_id,
                                     PartnerExporter)
    return partner_exporter.delete(record_id)
