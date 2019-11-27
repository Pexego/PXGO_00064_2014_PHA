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
        related='partner_id.commercial_partner_id', readonly=True)
    aux_mandate_id = fields.Many2one(comodel_name='account.banking.mandate',
                                     string='Banking mandate')
    aux_payment_mode_id = fields.Many2one(comodel_name='payment.mode',
                                          string='Payment mode')
    aux_payment_term = fields.Many2one(comodel_name='account.payment.term',
                                       string='Payment term')
    aux_date_due = fields.Date(string='Date due')

    @api.multi
    def write(self, vals):
        self.ensure_one()
        data = {}
        if 'aux_mandate_id' in vals:
            data['mandate_id'] = vals['aux_mandate_id']
        if 'aux_payment_mode_id' in vals:
            data['payment_mode_id'] = vals['aux_payment_mode_id']
        if 'aux_payment_term' in vals:
            data['payment_term'] = vals['aux_payment_term']
        if 'aux_date_due' in vals:
            data['date_due'] = vals['aux_date_due']
        self.invoice_id.write(data)
        res = super(AccountInvoiceSpecial, self).write(vals)
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def call_special_form(self):
        rec = self.env['account.invoice.special'].create({
            'invoice_id': self.id,
            'aux_mandate_id': self.mandate_id.id,
            'aux_payment_mode_id': self.payment_mode_id.id,
            'aux_payment_term': self.payment_term.id,
            'aux_date_due': self.date_due
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
