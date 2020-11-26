# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class AccountInvoiceSpecial(models.TransientModel):
    _name = 'account.invoice.special'
    _inherits = {'account.invoice': 'invoice_id'}

    invoice_id = fields.Many2one(comodel_name='account.invoice',
                                 required=True, ondelete='cascade')
    aux_partner_id = fields.Many2one(comodel_name='res.partner',
                                     string='Cliente/Proveedor')
    aux_commercial_partner_id = fields.Many2one(comodel_name='res.partner',
                                     string='Dirección facturación')
    aux_partner_shipping_id = fields.Many2one(comodel_name='res.partner',
                                     string='Direción envío')
    aux_customer_order = fields.Many2one(comodel_name='res.partner',
                                     string='Cliente pedido')
    aux_customer_payer = fields.Many2one(comodel_name='res.partner',
                                     string='Cliente pagador')
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
        for key in vals:
            data[key.replace('aux_', '')] = vals[key]
        self.invoice_id.write(data)
        res = super(AccountInvoiceSpecial, self).write(vals)
        return res


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def call_special_form(self):
        rec = self.env['account.invoice.special'].create({
            'invoice_id': self.id,
            'aux_partner_id': self.partner_id.id,
            'aux_commercial_partner_id': self.commercial_partner_id.id,
            'aux_partner_shipping_id': self.partner_shipping_id.id,
            'aux_customer_order': self.customer_order.id,
            'aux_customer_payer': self.customer_payer.id,
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
