# -*- coding: utf-8 -*-
# © 2022 Pharmadus Botanicals
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def facturae_detail(self):
        wizard_data = {
            'name': self.number,
            'invoice_id': self.id,
            'partner': self.partner_id.name,
        }

        invoice_id = self.env['facturae.invoice'].search([
            ('invoice_id', '=', self.id)
        ])
        if invoice_id:
            wizard_data['start_period'] = invoice_id.start_period
            wizard_data['end_period'] = invoice_id.end_period

        line_ids = []
        for line_id in self.invoice_line:
            line_ids += [(0, 0, {
                'invoice_line_id': line_id.id,
                'product_id': line_id.product_id.id,
                'description': line_id.name,
                'quantity': line_id.quantity
            })]
        wizard_data['line_ids'] = line_ids

        wizard = self.env['facturae.invoice.lines.wizard'].create(wizard_data)

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

    @api.multi
    def facturae_clear(self):
        self.env['facturae.invoice'].search([(['invoice_id', '=', self.id])]).\
            unlink()
        invoice_line_ids = [line_id.id for line_id in self.invoice_line]
        self.env['facturae.invoice.lines']. \
            search([('invoice_line_id', 'in', invoice_line_ids)]).unlink()
        return self.env['custom.views.warning'].show_message(
            'Factura-e',
            'Se han limpiado todos los datos de la factura-e'
        )
