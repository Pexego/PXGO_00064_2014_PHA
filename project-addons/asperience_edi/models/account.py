# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class AccountInvoiceLine(models.Model):

    _inherit = 'account.invoice.line'

    lot_id = fields.Many2one('stock.production.lot', 'Lot')
