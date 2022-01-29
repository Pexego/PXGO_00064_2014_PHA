# -*- coding: utf-8 -*-
# Copyright 2021 Manuel Regidor <manuel.regidor@sygel.es>
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from openerp import api, models


class AeatVatBookMapLines(models.Model):
    _inherit = "aeat.vat.book.map.line"

    @api.multi
    def _get_vat_book_taxes_map(self, company_id):
        self.ensure_one()
        s_iva_map_line = self.env.\
            ref("l10n_es_vat_book_backported.aeat_vat_book_map_line_s_iva")
        taxes = super(AeatVatBookMapLines, self).\
            _get_vat_book_taxes_map(company_id)
        if s_iva_map_line == self:
            taxes |= self.env["account.tax"].search(
                [
                    ("oss_country_id", "!=", False),
                    ("company_id", "=", company_id.id),
                ]
            )
        return taxes
