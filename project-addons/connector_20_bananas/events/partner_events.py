# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector.event import (
    on_record_create,
    on_record_unlink,
    on_record_write,
)
from openerp.addons.connector.queue.job import job
from openerp.addons.connector.unit.synchronizer import Exporter
from openerp.exceptions import Warning

from ..backend import bananas
from ..unit.backend_adapter import GenericAdapter
from .pricelist_events import (
    export_customer_rate,
    export_partner_pricelist,
    export_pricelist,
    unlink_partner_pricelist,
    insert_whitelist_item_job,
)
from .utils import _get_exporter, get_next_execution_time


@bananas
class PartnerExporter(Exporter):

    _model_name = ["res.partner"]

    def update(self, binding_id, mode):
        partner = self.model.browse(binding_id)
        if not partner.user_id and not partner.parent_id.user_id:
            raise Warning(
                "Comercial no encontrado para el cliente %s" % partner.name
            )
        vals = {
            "nombrecliente": partner.display_name,
            "codcliente": partner.bananas_id,
            "codcomercial": str(
                partner.user_id.id or partner.parent_id.user_id.id
            )
        }
        if mode == "insert":
            self.backend_adapter.insert(vals)

        else:
            return self.backend_adapter.update(binding_id, vals)

    def delete(self, binding_id):
        partner = self.model.browse(binding_id)
        self.backend_adapter.remove(partner.bananas_id)


@bananas
class PartnerAdapter(GenericAdapter):
    _model_name = "res.partner"
    _bananas_model = "clientes"


@on_record_create(model_names="res.partner")
def delay_export_partner_create(session, model_name, record_id, vals):
    partner = session.env[model_name].browse(record_id)
    if vals.get("bananas_synchronized") and vals.get("is_company"):
        partner.check_custom_pricelist(
            partner.commercial_discount, partner.financial_discount
        )
    elif (
        vals.get("parent_id")
        and partner.parent_id.bananas_synchronized
        and vals.get("type") == "delivery"
    ):
        partner.create_bananas_id()
    if vals.get("bananas_synchronized", False) and vals.get(
        "active", partner.active
    ):
        eta = get_next_execution_time(session)
        export_partner.delay(
            session, model_name, record_id, priority=1, eta=eta
        )
        if not partner.get_bananas_pricelist().bananas_synchronized:
            partner.get_bananas_pricelist().bananas_synchronized = True
            export_pricelist.delay(
                session, model_name, record_id, priority=2, eta=eta + 60
            )
            if partner.get_bananas_pricelist()._name == "product.pricelist":
                for item in partner.get_bananas_pricelist_items():
                    if not item.product_id.bananas_synchronized:
                        item.product_id.bananas_synchronized = True
                    export_customer_rate.delay(
                        session, item._name, item.id, priority=3, eta=eta + 90
                    )
        if not partner.partner_pricelist_exported:
            partner.partner_pricelist_exported = True
            export_partner_pricelist.delay(
                session, model_name, partner.id, priority=3, eta=eta + 80
            )


@on_record_write(model_names="res.partner")
def delay_export_partner_write(session, model_name, record_id, vals):
    if session.env.context.get("skip_conector"):
        return
    partner = session.env[model_name].browse(record_id)
    up_fields = [
        "name",
        "vat",
        "city",
        "street",
        "zip",
        "country_id",
        "ref",
        "user_id",
        "email",
        "phone",
        "mobile",
    ]
    eta = get_next_execution_time(session)
    if vals.get("bananas_synchronized", False) and vals.get(
        "active", partner.active
    ):
        export_partner.delay(
            session, model_name, record_id, priority=1, eta=eta
        )
        if not partner.get_bananas_pricelist().bananas_synchronized:
            partner.get_bananas_pricelist().bananas_synchronized = True
            export_pricelist.delay(
                session, model_name, record_id, priority=2, eta=eta + 60
            )
            if partner.get_bananas_pricelist()._name == "product.pricelist":
                for item in partner.get_bananas_pricelist_items():
                    if not item.product_id.bananas_synchronized:
                        item.product_id.bananas_synchronized = True
                    export_customer_rate.delay(
                        session, item._name, item.id, priority=3, eta=eta + 90
                    )
                    insert_whitelist_item_job.delay(
                        session,
                        "product.pricelist.item",
                        item.id,
                        partner.bananas_id,
                        item.product_id.id,
                        priority=3,
                        eta=eta + 90,
                    )
        partner.check_custom_pricelist(
            partner.commercial_discount, partner.financial_discount
        )
        if not partner.partner_pricelist_exported:
            partner.partner_pricelist_exported = True
            export_partner_pricelist.delay(
                session, model_name, partner.id, priority=3, eta=eta + 80
            )
    elif "bananas_synchronized" in vals and not vals["bananas_synchronized"]:
        if partner.partner_pricelist_exported:
            partner.partner_pricelist_exported = False
            unlink_partner_pricelist.delay(
                session, model_name, partner.id, priority=1, eta=eta
            )
        unlink_partner.delay(
            session, model_name, record_id, priority=3, eta=eta + 60
        )

    elif (
        partner.bananas_synchronized and "active" in vals and not vals["active"]
    ):
        if partner.partner_pricelist_exported:
            partner.partner_pricelist_exported = False
            unlink_partner_pricelist.delay(
                session, model_name, partner.id, priority=1, eta=eta
            )
        unlink_partner.delay(
            session, model_name, record_id, priority=3, eta=eta + 60
        )

    elif partner.bananas_synchronized and partner.active:
        if (
            vals
            and vals.get("property_product_pricelist")
            or "commercial_discount" in vals
            or "financial_discount" in vals
        ):
            unlink_partner_pricelist(session, model_name, partner.id)
            partner.check_custom_pricelist(
                partner.commercial_discount, partner.financial_discount
            )
            partner.with_context(
                skip_conector=True
            ).partner_pricelist_exported = False
        if not partner.get_bananas_pricelist().bananas_synchronized:
            partner.get_bananas_pricelist().bananas_synchronized = True
            export_pricelist.delay(
                session, model_name, record_id, priority=2, eta=eta + 60
            )
            if partner.get_bananas_pricelist()._name == "product.pricelist":
                for item in partner.get_bananas_pricelist_items():
                    if not item.product_id.bananas_synchronized:
                        item.product_id.bananas_synchronized = True
                    export_customer_rate.delay(
                        session, item._name, item.id, priority=3, eta=eta + 90
                    )
                    insert_whitelist_item_job.delay(
                        session,
                        "product.pricelist.item",
                        item.id,
                        partner.bananas_id,
                        item.product_id.id,
                        priority=3,
                        eta=eta + 90,
                    )
        if not partner.partner_pricelist_exported:
            partner.with_context(
                skip_conector=True
            ).partner_pricelist_exported = True
            export_partner_pricelist.delay(
                session, model_name, partner.id, priority=3, eta=eta + 80
            )
        for field in up_fields:
            if field in vals:
                update_partner.delay(
                    session, model_name, record_id, priority=2, eta=eta + 120
                )
                if partner.has_delivery_address:
                    for child in partner.child_ids.filtered(
                        lambda r: r.type == "delivery"
                    ):
                        update_partner.delay(
                            session,
                            model_name,
                            child.id,
                            priority=2,
                            eta=eta + 120,
                        )
                break


@on_record_unlink(model_names="res.partner")
def delay_unlink_partner(session, model_name, record_id):
    partner = session.env[model_name].browse(record_id)
    if partner.bananas_synchronized:
        partner.partner_pricelist_exported = False
        eta = get_next_execution_time(session)
        unlink_partner_pricelist.delay(
            session, model_name, partner.id, priority=1, eta=eta
        )
        unlink_partner.delay(
            session, model_name, record_id, priority=3, eta=eta + 60
        )


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def export_partner(session, model_name, record_id):
    partner_exporter = _get_exporter(
        session, model_name, record_id, PartnerExporter
    )
    return partner_exporter.update(record_id, "insert")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def update_partner(session, model_name, record_id):
    partner_exporter = _get_exporter(
        session, model_name, record_id, PartnerExporter
    )
    return partner_exporter.update(record_id, "update")


@job(retry_pattern={1: 10 * 60, 2: 20 * 60, 3: 30 * 60, 4: 40 * 60, 5: 50 * 60})
def unlink_partner(session, model_name, record_id):
    partner_exporter = _get_exporter(
        session, model_name, record_id, PartnerExporter
    )
    return partner_exporter.delete(record_id)
