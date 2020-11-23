# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
import time
from datetime import datetime
from time import mktime


class AccountInvoiceLine(models.Model):

    _inherit = "account.invoice.line"

    lot_id = fields.Many2one("stock.production.lot", "Lot")


class AccountInvoice(models.Model):

    _inherit = "account.invoice"
    customer_payer = fields.Many2one("res.partner")
    customer_order = fields.Many2one("res.partner")
    customer_department = fields.Char()

    @api.multi
    def _get_date_due_list(self):
        self.ensure_one()
        expiration_dates = []
        move_line_obj = self.env["account.move.line"]
        if self.move_id:
            move_lines = move_line_obj.search(
                [("move_id", "=", self.move_id.id), ("date_maturity", "!=", False)],
                order="date_maturity asc",
            )
            for line in move_lines:
                date = time.strptime(line.date_maturity, "%Y-%m-%d")
                date = datetime.fromtimestamp(mktime(date))
                date = date.strftime("%Y%m%d")
                expiration_dates.append(
                    (
                        date,
                        str(
                            self.type in ("out_invoice", "in_refund")
                            and line.debit
                            or (
                                self.type in ("in_invoice", "out_refund")
                                and line.credit
                                or 0
                            )
                        ),
                    )
                )

        return expiration_dates
