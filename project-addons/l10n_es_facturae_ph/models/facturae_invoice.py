# -*- coding: utf-8 -*-
# © 2023 Pharmadus Botanicals
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class FacturaeInvoice(models.Model):
    _name = 'facturae.invoice'

    invoice_id = fields.Integer(index=True)
    start_period = fields.Date('desde')
    end_period = fields.Date('a')


class FacturaeInvoiceLines(models.Model):
    _name = 'facturae.invoice.lines'

    invoice_id = fields.Integer(index=True)
    invoice_line_id = fields.Integer(index=True)
    contract_reference = fields.Char()
    transaction_reference = fields.Char()
