# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp.addons.connector_prestashop.models.stock_tracking.exporter import (
    PrestashopTrackingExporter,
)
from openerp.addons.connector_prestashop.backend import prestashop


@prestashop
class PrestashopTrackingExporterCustom(PrestashopTrackingExporter):
    def run(self, binding_id):
        pass
