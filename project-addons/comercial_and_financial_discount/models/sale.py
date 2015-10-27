# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013-Today Julius Network Solutions SARL <contact@julius.fr>
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
from openerp.exceptions import Warning

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    comercial_discount = fields.Boolean('Comercial discount', readonly=True)
    financial_discount = fields.Boolean('Financial discount', readonly=True)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    amount_gross_untaxed = fields.Float(
        'Amount',
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)
    article_discount = fields.Float(
        'Article discount',
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)
    amount_net_untaxed = fields.Float(
        'Net amount',
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)
    amount_subtotal_untaxed = fields.Float(
        'Subtotal',
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)

    comercial_discount_percentage = fields.Float(
        'Comercial discount percentage',
        readonly=True,
        states={'draft':[('readonly', False)], 'sent':[('readonly', False)]})
    comercial_discount_display = fields.Char(
        size = 32,
        compute='_comercial_discount_display')
    comercial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)

    financial_discount_percentage = fields.Float(
        'Financial discount percentage',
        readonly=True,
        states={'draft':[('readonly', False)], 'sent':[('readonly', False)]})
    financial_discount_display = fields.Char(
        size=32,
        compute='_financial_discount_display')
    financial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)

    amount_tax_with_discounts = fields.Float(
        'Taxes',
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)
    amount_total_with_discounts = fields.Float(
        'Total',
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)

    @api.one
    @api.depends('amount_untaxed',
                 'amount_tax',
                 'order_line',
                 'order_line.product_uom_qty',
                 'order_line.price_unit',
                 'order_line.discount',
                 'comercial_discount_percentage',
                 'financial_discount_percentage')
    def _calculate_amounts(self):
        discount_art = 0
        for line in self.order_line:
            discount_art = discount_art + \
                  (line.product_uom_qty * line.price_unit * line.discount / 100)
        self.article_discount = discount_art
        self.amount_gross_untaxed = self.amount_untaxed + discount_art

        discount_com = (100 - self.comercial_discount_percentage) / 100
        self.comercial_discount_amount = self.amount_untaxed - \
                                         self.amount_untaxed * discount_com

        self.amount_net_untaxed = self.amount_untaxed - \
                                  self.comercial_discount_amount

        discount_fin = (100 - self.financial_discount_percentage) / 100
        self.financial_discount_amount = self.amount_net_untaxed - \
                                         self.amount_net_untaxed * discount_fin

        self.amount_subtotal_untaxed = self.amount_untaxed - \
                                       self.comercial_discount_amount - \
                                       self.financial_discount_amount

        discount = (100 - self.financial_discount_percentage -
                    self.comercial_discount_percentage) / 100
        self.amount_tax_with_discounts = self.amount_tax * discount
        self.amount_total_with_discounts = \
            (self.amount_untaxed * discount) + \
            self.amount_tax_with_discounts

    @api.one
    @api.depends('comercial_discount_percentage')
    def _comercial_discount_display(self):
        self.comercial_discount_display = _('Commercial discount') +\
                                          ' (%.2f %%) :'\
                                          %self.comercial_discount_percentage

    @api.one
    @api.constrains('comercial_discount_percentage')
    def _check_comercial_discount_percentage(self):
        if self.comercial_discount_percentage and \
            (self.comercial_discount_percentage < 0 or \
            self.comercial_discount_percentage > 100):
            raise Warning(_('Discount value should be between 0 and 100'))

    @api.one
    @api.depends('financial_discount_percentage')
    def _financial_discount_display(self):
        self.financial_discount_display = _('Financial discount') +\
                                          ' (%.2f %%) :'\
                                          %self.financial_discount_percentage

    @api.one
    @api.constrains('financial_discount_percentage')
    def _check_financial_discount_percentage(self):
        if self.financial_discount_percentage and \
            (self.financial_discount_percentage < 0 or \
            self.financial_discount_percentage > 100):
            raise Warning(_('Discount value should be between 0 and 100'))

    @api.one
    def _get_lines_by_taxes(self, lines=None):
        """ This method will return a dictionary of taxes as keys
        with the related lines.
        """
        if lines is None:
            lines = self.order_line
        res = {}
        for line in lines:
            taxes = [x.id for x in line.tax_id]
            if taxes:
                taxes.sort()
            taxes_str = str(taxes)
            res.setdefault(taxes_str, [])
            res[taxes_str].append(line)
        return res

    @api.one
    def _create_comercial_lines_discount_by_taxes(self, line_by_taxes):
        discount = self.comercial_discount_percentage / 100
        product = self.env.ref('comercial_and_financial_discount.product_comercial_discount')
        line_obj = self.env['sale.order.line']
        if isinstance(line_by_taxes, list):
            line_by_taxes = line_by_taxes and line_by_taxes[0] or {}
        for tax_str in line_by_taxes.keys():
            line_sum = 0
            discount_value = 0
            order = False
            line = False
            for line in line_by_taxes[tax_str]:
                qty = line.product_uom_qty
                sub = line.price_subtotal
                line_sum += sub
                discount_value = line_sum * discount
            if line:
                res_value = line_obj.\
                    product_id_change(pricelist=self.pricelist_id.id,
                                      product=product.id, qty=1,
                                      partner_id=self.partner_id.id,
                                      lang=self.partner_id.lang,
                                      update_tax=False,
                                      date_order=self.date_order,
                                      fiscal_position=self.fiscal_position)
                value = res_value.get('value')
                if value:
                    tax_ids = eval(tax_str)
                    tax_ids = [(6, 0, tax_ids)]
                    value.update({
                        'comercial_discount': True,
                        'price_unit': -discount_value,
                        'order_id': self.id,
                        'product_id': product.id,
                        'product_uos_qty': 1,
                        'tax_id': tax_ids, 
                    })
                    new_line = line_obj.create(value)
                    new_line.product_uom_qty = 1

    @api.one
    def generate_comercial_discount(self):
        if self.state in ('draft','sent') and \
            self.comercial_discount_percentage != 0.00:
            domain = [
                ('order_id', '=', self.id),
                ('comercial_discount', '=', True),
                ('state', '=', 'draft'),
                ]
            line_obj = self.env['sale.order.line']
            lines = line_obj.search(domain)
            if lines:
                lines.unlink()
            line_by_taxes = self._get_lines_by_taxes()
            self._create_comercial_lines_discount_by_taxes(line_by_taxes)
            self.comercial_discount_percentage = 0

    def _make_invoice(self, cr, uid, order, lines, context=None):
        inv_id = super(SaleOrder, self)._make_invoice(cr, uid, order, lines,
                                                      context=None)
        if order.comercial_discount_percentage:
#            invoice_obj = self.env['account.invoice']
            inv_id.generate_comercial_discount(
                order.comercial_discount_percentage)
        return inv_id
#            invoice_obj.generate_comercial_discount(cr, uid, [inv_id],
#                                            order.comercial_discount_percentage,
#                                            context=context)

    @api.one
    def generate_financial_discount(self):
        line_obj = self.env['sale.order.line']
        if self.state in ('draft', 'sent') and \
           self.financial_discount_percentage != 0.00:
            discount = self.financial_discount_percentage / 100
            res = 0
            for line in self.order_line:
                if line.financial_discount:
                    line_obj.unlink([line.id])
                else:
                    qty = line.product_uom_qty
                    pu = line.price_unit
                    sub = qty * pu
                    res += sub
            discount_value = res * discount
            product_id = self.env.ref(
                'comercial_and_financial_discount.product_financial_discount')
            res = line_obj.product_id_change([],
                pricelist=self.pricelist_id.id,
                product=product_id, qty=1,
                partner_id=self.partner_id.id,
                lang=self.partner_id.lang, update_tax=True,
                date_order=self.date_order,
                fiscal_position=self.fiscal_position)
            value = res.get('value')
            if value:
                tax_ids = value.get('tax_id') and \
                    [(6, 0, value.get('tax_id'))] or [(6, 0, [])]
                value.update({
                    'financial_discount': True,
                    'price_unit': -discount_value,
                    'order_id': self.id,
                    'product_id': product_id,
                    'product_uom_qty': 1,
                    'product_uos_qty': 1,
                    'tax_id': tax_ids,
                })
                line_obj.create(value)
                self.financial_discount_percentage = 0.00
        return True

    @api.one
    def generate_discounts(self):
        # Generate discounts in correct order
        self.generate_comercial_discount()
        self.generate_financial_discount()
