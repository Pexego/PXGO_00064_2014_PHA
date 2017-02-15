# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    sale_channel_id = fields.Many2one('sale.channel', 'Sale channel')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move,
                          context=None):
        inv_vals = super(StockPicking, self).\
            _get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context)
        sale = move.picking_id.sale_id
        if sale:
            inv_vals.update({'sale_channel_id': sale.sale_channel_id.id})
        return inv_vals
