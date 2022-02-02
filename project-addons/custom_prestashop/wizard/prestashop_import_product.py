# -*- coding: utf-8 -*-
# © 2022 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from openerp.addons.connector_prestashop.unit.importer import import_record
from openerp.addons.connector.session import ConnectorSession


class PrestashopImportProduct(models.TransientModel):
    _name = "prestashop.import.product"

    prestashop_id = fields.Integer(string="Id", required=True)

    @api.multi
    def import_product(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context)
        backend_ids = self.env["prestashop.backend"].browse(
            self.env.context.get("active_ids")
        )
        for backend in backend_ids:
            import_record.delay(
                    session, 'prestashop.product.template',
                    backend.id, self.prestashop_id)

        return {"type": "ir.actions.act_window_close"}
