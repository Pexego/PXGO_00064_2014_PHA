# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models
from openerp.addons.connector_prestashop.models.delivery_carrier.common import (
    DeliveryCarrierAdapter,
)
from openerp.addons.connector_prestashop.backend import prestashop


class DeliveryCarrier(models.Model):

    _inherit = "delivery.carrier"

    prestashop_carrier_ids = fields.Char(
        help="Prestashop ID of carrier separated by comma"
    )


class PrestashopDeliveryCarrier(models.Model):
    _inherit = "prestashop.delivery.carrier"

    def init(self, cr):
        cr.execute(
            "alter table prestashop_delivery_carrier "
            "drop constraint if exists prestashop_delivery_carrier_prestashop_erp_uniq"
        )
        return True


@prestashop(replacing=DeliveryCarrierAdapter)
class DeliveryCarrierAdapterCustom(DeliveryCarrierAdapter):
    def search(self, filters=None):
        if filters is None:
            filters = {}
        filters["filter[active]"] = 1
        return super(DeliveryCarrierAdapterCustom, self).search(filters)
