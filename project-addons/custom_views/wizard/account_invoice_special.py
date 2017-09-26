# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class AccountInvoiceSpecial(models.TransientModel):
    _name = 'account.invoice.special'
    _inherits = {'account.invoice': 'invoice_id'}

    invoice_id = fields.Many2one(comodel_name='account.invoice',
                                 required=True, ondelete='cascade')
    commercial_partner_id = fields.Many2one(
        related='partner_id.commercial_partner_id')
    aux_mandate_id = fields.Many2one(comodel_name='account.banking.mandate',
                                     string='Banking mandate')
    aux_payment_term = fields.Many2one(comodel_name='account.payment.term',
                       string='Payment term')

    @api.multi
    def write(self, vals):
        res = super(AccountInvoiceSpecial, self).write(vals)
        for s in self:
            s.invoice_id.mandate_id = s.aux_mandate_id
            s.invoice_id.payment_term = s.aux_payment_term
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def call_special_form(self):
        rec = self.env['account.invoice.special'].create({
            'invoice_id': self.id,
            'aux_mandate_id': self.mandate_id.id,
            'aux_payment_term': self.payment_term.id
        })
        view_id = self.env.ref('custom_views.view_invoice_special_form').id

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.invoice.special',
            'view_id': view_id,
            'res_id': rec.id,
            'target': 'current'
        }
