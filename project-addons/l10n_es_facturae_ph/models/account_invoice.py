# -*- coding: utf-8 -*-
# © 2022 Pharmadus Botanicals
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def facturae_lines(self):
        line_ids = []
        for line_id in self.invoice_line:
            line_ids += [(0, 0, {
                'invoice_line_id': line_id.id,
                'product_id': line_id.product_id.id,
                'description': line_id.name,
                'quantity': line_id.quantity
            })]

        wizard = self.env['facturae.invoice.lines.wizard'].create({
            'name': self.number,
            'partner': self.partner_id.name,
            'line_ids': line_ids
        })

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': wizard._name,
            'res_id': wizard.id,
            'target': 'new',
            'flags': {'initial_mode': 'edit'},
            'context': self.env.context
        }