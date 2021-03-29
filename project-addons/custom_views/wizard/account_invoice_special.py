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
    aux_customer_department = fields.Char(string='Departamento')
    aux_name = fields.Char(string='Referencia / Descripción')
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
        wizard = self.env['account.invoice.special']
        data = {'invoice_id': self.id}
        for column in wizard._columns:
            if column[:4] == 'aux_':
                if wizard._columns[column]._type == 'many2one':
                    data[column] = eval('self.' + column[4:] + '.id')
                else:
                    data[column] = eval('self.' + column[4:])
        rec = wizard.create(data)
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
