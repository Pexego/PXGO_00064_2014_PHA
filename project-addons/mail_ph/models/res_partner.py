# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import ValidationError
from ..validations import is_valid_email


class ResPartner(models.Model):
    _inherit = 'res.partner'

    invoice_claims_mail = fields.Char()
    purchases_mail = fields.Char()
    sales_mail = fields.Char()
    transfer_sales_mail = fields.Char()
    transfer_wholesaler = fields.Boolean(compute='_is_transfer_wholesaler')
    clean_fax_number = fields.Char(compute='_clean_fax_number')

    @api.onchange('email_to_send_invoice')
    def check_email_to_send_invoice(self):
        if self.email_to_send_invoice:
            if ';' in self.email_to_send_invoice:
                self.email_to_send_invoice = \
                    self.email_to_send_invoice.replace(';', ',')
            if not is_valid_email(self.email_to_send_invoice):
                raise ValidationError(_('Not a valid e-mail to send invoice'))

    @api.onchange('invoice_claims_mail')
    def check_invoice_claims_mail(self):
        if self.invoice_claims_mail:
            if ';' in self.invoice_claims_mail:
                self.invoice_claims_mail = \
                    self.invoice_claims_mail.replace(';', ',')
            if not is_valid_email(self.invoice_claims_mail):
                raise ValidationError(_('Not a valid invoice claims e-mail'))

    @api.onchange('purchases_mail')
    def check_purchases_mail(self):
        if self.purchases_mail:
            if ';' in self.purchases_mail:
                self.purchases_mail = self.purchases_mail.replace(';', ',')
            if not is_valid_email(self.purchases_mail):
                raise ValidationError(_('Not a valid purchases e-mail'))

    @api.onchange('sales_mail')
    def check_sales_mail(self):
        if self.sales_mail:
            if ';' in self.sales_mail:
                self.sales_mail = self.sales_mail.replace(';', ',')
            if not is_valid_email(self.sales_mail):
                raise ValidationError(_('Not a valid sales e-mail'))

    @api.onchange('transfer_sales_mail')
    def check_transfer_sales_mail(self):
        if self.transfer_sales_mail:
            if ';' in self.transfer_sales_mail:
                self.transfer_sales_mail = \
                    self.transfer_sales_mail.replace(';', ',')
            if not is_valid_email(self.transfer_sales_mail):
                raise ValidationError(_('Not a valid transfer sales e-mail'))

    @api.one
    def _is_transfer_wholesaler(self):
        self.transfer_wholesaler = self.env.ref('.et010') in self.category_id

    @api.one
    def _clean_fax_number(self):
        # This cleaner only works for Spain phone numbers
        fax = self.fax
        if fax:
            fax = fax.strip().replace(' ', '')
            if fax[0:3] == '+34':
                fax = fax[3:]
            elif fax[0:4] == '0034':
                fax = fax[4:]
        self.clean_fax_number = fax