# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from datetime import date, datetime, timedelta

from openerp import api, fields, models
from openerp.addons.connector.session import ConnectorSession

from ..events.sale_events import sale_order_import_batch


class BananasBackend(models.Model):
    _name = "bananas.backend"
    _inherit = "connector.backend"
    _backend_type = "bananas"

    @api.model
    def _select_versions(self):
        return [("1.6", "20 bananas 1.6")]

    name = fields.Char(required=True)
    location = fields.Char(required=True, help="Url to 20 bananas api")
    api_key = fields.Char(required=True)
    version = fields.Selection(selection="_select_versions", required=True)
    order_message = fields.Char(
        help="you can use the format key {order} to se the order number into the message"
    )
    import_orders_from_date = fields.Date()
    start_execution_hour = fields.Integer()
    stop_execution_hour = fields.Integer()

    @api.multi
    def import_sale_orders(self):
        session = ConnectorSession(
            self.env.cr, self.env.uid, context=self.env.context
        )
        if not self.import_orders_from_date:
            curr_date = date.today() + timedelta(days=-30)
        else:
            curr_date = datetime.strptime(
                self.import_orders_from_date, "%Y-%m-%d"
            ).date()
        today = date.today()
        while curr_date <= today:
            sale_order_import_batch.delay(
                session,
                "sale.order",
                self.id,
                curr_date.strftime("%Y-%m-%d"),
                priority=1,
            )
            curr_date = curr_date + timedelta(days=1)
        self.import_orders_from_date = date.today()

    @api.model
    def import_sale_orders_cron(self):
        for conf in self.env["bananas.backend"].search([]):
            conf.import_sale_orders()
