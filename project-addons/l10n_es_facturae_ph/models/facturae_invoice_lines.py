# -*- coding: utf-8 -*-
# © 2022 Pharmadus Botanicals
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, fields


class FacturaeInvoiceLines(models.Model):
    _name = 'facturae.invoice.lines'

    invoice_line_id = fields.Integer(index=True)
    contract_reference = fields.Char()
    transaction_reference = fields.Char()
