# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import api, models


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    @api.multi
    def _get_sii_line_price_unit(self):
        self.ensure_one()
        # Line discount
        price_unit = self.price_unit * (1 - (self.discount or 0.0) / 100.0)

        # Commercial discount
        price_unit = price_unit * (1 - (self.commercial_discount or 0.0) / 100)

        # Financial discount
        price_unit = price_unit * (1 - (self.financial_discount or 0.0) / 100)

        # Currency conversion
        if self.invoice_id.currency_id != \
                self.invoice_id.company_id.currency_id:
            from_currency = self.invoice_id.currency_id.\
                with_context(date=self.invoice_id.date_invoice)
            price_unit = from_currency.\
                compute(price_unit, self.invoice_id.company_id.currency_id)
        return price_unit