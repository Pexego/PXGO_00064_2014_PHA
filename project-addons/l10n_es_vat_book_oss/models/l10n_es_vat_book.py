# -*- coding: utf-8 -*-
# Copyright 2021 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import models


class L10nEsVatBook(models.Model):
    _inherit = "l10n.es.vat.book.backport"

    def _prepare_book_line_tax_vals(self, move_line, vat_book_line, taxes):
        values = super(L10nEsVatBook, self)._prepare_book_line_tax_vals(
            move_line, vat_book_line, taxes
        )
        oss_taxes = self.env["account.tax"].search(
            [("oss_country_id", "!=", False),
             ("company_id", "=", self.company_id.id)]
        )
        if move_line.invoice_line_tax_id.filtered(lambda x: x in oss_taxes):
            for vals in values:
                if vals.get('tax_id') in oss_taxes.ids:
                    vals.update({"tax_amount": 0,
                                 "total_amount": vals.get("base_amount")})
        return values
