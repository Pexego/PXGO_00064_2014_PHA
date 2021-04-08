# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector_prestashop.models.delivery_carrier.importer import (
    CarrierImportMapper,
)
from openerp.addons.connector_prestashop.backend import prestashop
from openerp.addons.connector.unit.mapper import mapping, only_create


@prestashop(replacing=CarrierImportMapper)
class CarrierImportMapperCustom(CarrierImportMapper):
    direct = []

    @mapping
    def active(self, record):
        pass

    @mapping
    def product_id(self, record):
        pass

    @mapping
    def partner_id(self, record):
        pass

    @mapping
    def prestashop_id(self, record):
        return {"prestashop_id": record["id"]}

    @mapping
    def backend_id(self, record):
        return {"backend_id": self.backend_record.id}

    @mapping
    def company_id(self, record):
        pass

    @mapping
    @only_create
    def odoo_id(self, record):
        use_carrier = False
        carriers = self.env["delivery.carrier"].search(
            [("prestashop_carrier_ids", "ilike", record["id"])]
        )
        if carriers:
            for carrier in carriers:
                if record["id"] in carrier.prestashop_carrier_ids.split(","):
                    use_carrier = carrier
        if use_carrier:
            return {"odoo_id": use_carrier.id}
        raise Exception("carrier not found for prestashop id {}".format(record["id"]))
