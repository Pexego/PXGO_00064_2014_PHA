# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, api, fields
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT as DATETIME_FORMAT
import datetime


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    latest_calculations = fields.Datetime(
            'Latest date and time when amounts were calculated')
    banking_mandate_needed = fields.Boolean(
            related='payment_mode_id.banking_mandate_needed')

    @api.model
    def create(self, vals):
        res = super(AccountInvoice, self).create(vals)
        # Trigger write event to force re-calculations after create and to
        # check if payment mode need a banking mandate, to assign it
        # automatically if it is possible.
        res.state = res.state
        return res

    @api.multi
    def write(self, vals):
        # Check if banking mandate is needed and populate it if the partner has
        # one and only one. If the partner has several mandates, the view will
        # force the user to choose one.
        for invoice in self:
            if invoice.payment_mode_id and \
               invoice.payment_mode_id.banking_mandate_needed and \
               not vals.get('mandate_id', invoice.mandate_id.id):
                partner_id = vals.get('partner_id', False)
                if partner_id:
                    partner = self.env['partner_id'].browse(partner_id)
                else:
                    partner = invoice.partner_id

                # If the partner has not a bank and has a parent partner,
                # assign parent bank(s) instead
                if not partner.bank_ids and partner.parent_id.bank_ids:
                    banks = partner.parent_id.bank_ids
                else:
                    banks = partner.bank_ids
                if banks:
                    mandates = []
                    for bank in banks:
                        for mandate in bank.mandate_ids:
                            mandates.append(mandate)
                    if len(mandates) == 1:
                        invoice.mandate_id = mandates[0]

        # Force re-calculations on save
        re_calculate = False
        type_is_out_invoice = True
        if not vals.get('latest_calculations'):
            for rec in self:
                now = datetime.datetime.now()
                if rec.latest_calculations:
                    then = datetime.datetime.strptime(rec.latest_calculations,
                                                      DATETIME_FORMAT)
                else:
                    then = now - datetime.timedelta(days=1)

                diff = now - then
                re_calculate = re_calculate or \
                               diff.days > 0 or \
                               diff.seconds > 10
                type_is_out_invoice = type_is_out_invoice and \
                                      (rec.type == 'out_invoice')

        if re_calculate and type_is_out_invoice:
            # Timestamp to avoid unnecessary loops
            vals['latest_calculations'] = fields.Datetime.now()
            res = super(AccountInvoice, self).write(vals)
            self.button_reset_taxes()
        else:
            res = super(AccountInvoice, self).write(vals)

        return res


class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    invoice_type = fields.Selection([
            ('out_invoice','Customer Invoice'),
            ('in_invoice','Supplier Invoice'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
        ], related='invoice_id.type')

    @api.multi
    def product_id_change(self, product, uom_id, qty=0, name='', type='out_invoice',
            partner_id=False, fposition_id=False, price_unit=False, currency_id=False,
            company_id=None):
        res = super(AccountInvoiceLine, self).product_id_change(product,
                uom_id, qty, name, type, partner_id, fposition_id, price_unit,
                currency_id, company_id)
        product_name = self.env['product.product'].browse(product).name_template
        res['value']['name'] = product_name
        return res
