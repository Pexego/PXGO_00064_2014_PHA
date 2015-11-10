# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
#    $Oscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, api, fields, _
import openerp.addons.decimal_precision as dp
from datetime import datetime, timedelta

class AccountInvoiceLine(models.Model):
    _inherit = 'account.invoice.line'

    price_subtotal = fields.Float(
        'Subtotal',
        compute='_compute_price',
        digits_compute= dp.get_precision('Account'),
        store=True,
        readonly=True)
    gross_amount = fields.Float(
        'Gross amount',
        compute='_compute_price',
        digits_compute= dp.get_precision('Account'),
        store=True,
        readonly=True)
    discount_amount = fields.Float(
        'Discount amount',
        compute='_compute_price',
        digits_compute= dp.get_precision('Account'),
        store=True,
        readonly=True)
    discounted_amount = fields.Float(
        'Discounted amount',
        compute='_compute_price',
        digits_compute= dp.get_precision('Account'),
        store=True,
        readonly=True)
    commercial_discount = fields.Float(
        'Commercial discount (%)',
        digits_compute=dp.get_precision('Discount'),
        readonly=True,
        default=0.0,
        states={'draft': [('readonly', False)]})
    financial_discount = fields.Float('Financial discount (%)',
        digits_compute=dp.get_precision('Discount'),
        readonly=True,
        default=0.0,
        states={'draft': [('readonly', False)]})
    move_id = fields.Many2one(
        comodel_name='stock.move',
        readonly=True)

    @api.one
    @api.depends('price_unit', 'discount', 'commercial_discount',
                'financial_discount', 'invoice_line_tax_id', 'quantity',
                'product_id', 'invoice_id.partner_id', 'invoice_id.currency_id')
    def _compute_price(self):
        price = self.price_unit * (1 - (self.discount or 0.0) / 100.0) * \
                (1 - (self.commercial_discount or 0.0) / 100.0) * \
                (1 - (self.financial_discount or 0.0) / 100.0)
        taxes = self.invoice_line_tax_id.compute_all(price, self.quantity,
                    product=self.product_id, partner=self.invoice_id.partner_id)
        self.gross_amount = self.price_unit * self.quantity
        self.discount_amount = self.gross_amount - price * self.quantity
        self.discounted_amount = self.price_unit * self.quantity * \
                                 (1 - (self.discount or 0.0) / 100.0)
        self.price_subtotal = taxes['total']
        if self.invoice_id:
            self.price_subtotal = self.invoice_id.currency_id.round(
                self.price_subtotal)

    @api.model
    def _default_price_unit(self):
        if not self._context.get('check_total'):
            return 0
        total = self._context['check_total']
        for l in self._context.get('invoice_line', []):
            if isinstance(l, (list, tuple)) and len(l) >= 3 and l[2]:
                vals = l[2]
                price = vals.get('price_unit', 0) * \
                        (1 - vals.get('discount', 0) / 100.0) * \
                        (1 - vals.get('commercial_discount', 0) / 100.0) * \
                        (1 - vals.get('financial_discount', 0) / 100.0)
                total = total - (price * vals.get('quantity'))
                taxes = vals.get('invoice_line_tax_id')
                if taxes and len(taxes[0]) >= 3 and taxes[0][2]:
                    taxes = self.env['account.tax'].browse(taxes[0][2])
                    tax_res = taxes.compute_all(price, vals.get('quantity'),
                        product=vals.get('product_id'),
                        partner=self._context.get('partner_id'))
                    for tax in tax_res['taxes']:
                        total = total - tax['amount']
        return total

    @api.model
    def move_line_get(self, invoice_id):
        inv = self.env['account.invoice'].browse(invoice_id)
        currency = inv.currency_id.with_context(date=inv.date_invoice)
        company_currency = inv.company_id.currency_id

        res = []
        for line in inv.invoice_line:
            mres = self.move_line_get_item(line)
            mres['invl_id'] = line.id
            res.append(mres)
            tax_code_found = False
            taxes = line.invoice_line_tax_id.compute_all(
                (line.price_unit * (1.0 - (line.discount or 0.0) / 100.0) * \
                (1 - (line.commercial_discount or 0.0) / 100.0) * \
                (1 - (line.financial_discount or 0.0) / 100.0)),
                line.quantity, line.product_id, inv.partner_id)['taxes']
            for tax in taxes:
                if inv.type in ('out_invoice', 'in_invoice'):
                    tax_code_id = tax['base_code_id']
                    tax_amount = tax['price_unit'] * line.quantity * \
                                 tax['base_sign']
                else:
                    tax_code_id = tax['ref_base_code_id']
                    tax_amount = tax['price_unit'] * line.quantity * \
                                 tax['ref_base_sign']

                if tax_code_found:
                    if not tax_code_id:
                        continue
                    res.append(dict(mres))
                    res[-1]['price'] = 0.0
                    res[-1]['account_analytic_id'] = False
                elif not tax_code_id:
                    continue
                tax_code_found = True

                res[-1]['tax_code_id'] = tax_code_id
                res[-1]['tax_amount'] = currency.compute(tax_amount,
                                                         company_currency)
        return res


class AccountInvoiceTax(models.Model):
    _inherit = "account.invoice.tax"

    @api.v8
    def compute(self, invoice):
        tax_grouped = {}
        currency = invoice.currency_id.with_context(date=invoice.date_invoice or fields.Date.context_today(invoice))
        company_currency = invoice.company_id.currency_id
        for line in invoice.invoice_line:
            taxes = line.invoice_line_tax_id.compute_all(
                (line.price_unit * (1 - (line.discount or 0.0) / 100.0) * \
                (1 - (line.commercial_discount or 0.0) / 100.0) * \
                (1 - (line.financial_discount or 0.0) / 100.0)),
                line.quantity, line.product_id, invoice.partner_id)['taxes']
            for tax in taxes:
                val = {
                    'invoice_id': invoice.id,
                    'name': tax['name'],
                    'amount': tax['amount'],
                    'manual': False,
                    'sequence': tax['sequence'],
                    'base': currency.round(tax['price_unit'] * line['quantity']),
                }
                if invoice.type in ('out_invoice','in_invoice'):
                    val['base_code_id'] = tax['base_code_id']
                    val['tax_code_id'] = tax['tax_code_id']
                    val['base_amount'] = currency.compute(val['base'] * tax['base_sign'], company_currency, round=False)
                    val['tax_amount'] = currency.compute(val['amount'] * tax['tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_collected_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_collected_id']
                else:
                    val['base_code_id'] = tax['ref_base_code_id']
                    val['tax_code_id'] = tax['ref_tax_code_id']
                    val['base_amount'] = currency.compute(val['base'] * tax['ref_base_sign'], company_currency, round=False)
                    val['tax_amount'] = currency.compute(val['amount'] * tax['ref_tax_sign'], company_currency, round=False)
                    val['account_id'] = tax['account_paid_id'] or line.account_id.id
                    val['account_analytic_id'] = tax['account_analytic_paid_id']

                # If the taxes generate moves on the same financial account as the invoice line
                # and no default analytic account is defined at the tax level, propagate the
                # analytic account from the invoice line to the tax line. This is necessary
                # in situations were (part of) the taxes cannot be reclaimed,
                # to ensure the tax move is allocated to the proper analytic account.
                if not val.get('account_analytic_id') and line.account_analytic_id and val['account_id'] == line.account_id.id:
                    val['account_analytic_id'] = line.account_analytic_id.id

                key = (val['tax_code_id'], val['base_code_id'], val['account_id'])
                if not key in tax_grouped:
                    tax_grouped[key] = val
                else:
                    tax_grouped[key]['base'] += val['base']
                    tax_grouped[key]['amount'] += val['amount']
                    tax_grouped[key]['base_amount'] += val['base_amount']
                    tax_grouped[key]['tax_amount'] += val['tax_amount']

        for t in tax_grouped.values():
            t['base'] = currency.round(t['base'])
            t['amount'] = currency.round(t['amount'])
            t['base_amount'] = currency.round(t['base_amount'])
            t['tax_amount'] = currency.round(t['tax_amount'])

        return tax_grouped


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    amount_gross_untaxed = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    article_discount = fields.Float(
        'Article discount',
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    amount_with_article_discount = fields.Float(
        'Amount with article discount',
        compute='_compute_amount',
        store=True,
        readonly=True)
    amount_net_untaxed = fields.Float(
        'Net amount',
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    commercial_discount_display = fields.Char(
        size = 32,
        compute='_compute_amount',
        store=True,
        readonly=True)
    commercial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)
    financial_discount_display = fields.Char(
        size=32,
        compute='_compute_amount',
        store=True,
        readonly=True)
    financial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_compute_amount',
        store=True,
        readonly=True)

    @api.one
    @api.depends('invoice_line.price_subtotal', 'tax_line.amount')
    def _compute_amount(self):
        amount_untaxed = 0
        amount_gross = 0
        art_disc_amount = 0
        com_discount = 0
        com_disc_amount = 0
        fin_discount = 0
        fin_disc_amount = 0
        for line in self.invoice_line:
            amount_untaxed += line.price_subtotal
            amount = line.quantity * line.price_unit
            amount_gross += amount
            art_disc_amount += amount * line.discount / 100
            aux = amount * (1 - line.discount / 100)
            com_discount = line.commercial_discount
            com_disc_amount += aux * com_discount / 100
            aux = aux * (1 - com_discount / 100)
            fin_discount = line.financial_discount
            fin_disc_amount += aux * fin_discount / 100

        self.amount_gross_untaxed = amount_gross
        self.article_discount = art_disc_amount
        self.amount_with_article_discount = amount_gross - art_disc_amount
        self.commercial_discount_amount = com_disc_amount
        self.amount_net_untaxed = amount_gross - art_disc_amount - \
                                  com_disc_amount
        self.financial_discount_amount = fin_disc_amount
        self.amount_untaxed = amount_untaxed
        self.amount_tax = sum(line.amount for line in self.tax_line)
        self.amount_total = self.amount_untaxed + self.amount_tax

        if com_discount > 0:
            self.commercial_discount_display = \
                _('Commercial discount (%.2f %%) :')%com_discount
        else:
            self.commercial_discount_display = _('Commercial discount :')

        if fin_discount > 0:
            self.financial_discount_display = \
                _('Financial discount (%.2f %%) :')%fin_discount
        else:
            self.financial_discount_display = _('Financial discount :')
