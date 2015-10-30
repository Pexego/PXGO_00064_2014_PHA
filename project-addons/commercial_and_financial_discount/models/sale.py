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

    commercial_discount = fields.Boolean('Commercial discount', readonly=True)
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
    commercial_discount_input = fields.Float(
        'Commercial discount percentage',
        readonly=True,
        states={'draft':[('readonly', False)], 'sent':[('readonly', False)]})
    commercial_discount_percentage = fields.Float(readonly=True)
    commercial_discount_display = fields.Char(
        size = 32,
        compute='_commercial_discount_display')
    commercial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)
    financial_discount_input = fields.Float(
        'Financial discount percentage',
        readonly=True,
        states={'draft':[('readonly', False)], 'sent':[('readonly', False)]})
    financial_discount_percentage = fields.Float(readonly=True)
    financial_discount_display = fields.Char(
        size=32,
        compute='_financial_discount_display')
    financial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)

    def onchange_partner_id(self, cr, uid, ids, partner_id, context):
        res = super(SaleOrder, self).onchange_partner_id(cr, uid, ids,
                                                         partner_id, context)
        partner = self.pool.get('res.partner').browse(cr, uid, partner_id)
        res['value'].update({
            'commercial_discount_input': partner.commercial_discount,
            'financial_discount_input': partner.financial_discount
        })
        return res

    @api.one
    @api.depends('amount_untaxed',
                 'amount_tax',
                 'order_line',
                 'order_line.product_uom_qty',
                 'order_line.price_unit',
                 'order_line.discount',
                 'commercial_discount_percentage',
                 'financial_discount_percentage')
    def _calculate_amounts(self):
        amount_gross = 0
        discount_art = 0
        com_disc_amount = 0
        fin_disc_amount = 0
        for line in self.order_line:
            if line.commercial_discount:
                com_disc_amount += line.price_unit
            elif line.financial_discount:
                fin_disc_amount += line.price_unit
            else:
                amount_gross += line.product_uom_qty * line.price_unit
                discount_art = discount_art + \
                      (line.product_uom_qty * line.price_unit *
                       line.discount / 100)
        self.amount_gross_untaxed = amount_gross
        self.article_discount = discount_art
        self.commercial_discount_amount = com_disc_amount
        self.amount_net_untaxed = amount_gross - discount_art + \
                                  self.commercial_discount_amount
        self.financial_discount_amount = fin_disc_amount

    @api.one
    @api.depends('commercial_discount_percentage')
    def _commercial_discount_display(self):
        if self.commercial_discount_percentage > 0:
            self.commercial_discount_display = \
                _('Commercial discount (%.2f %%) :')\
                %self.commercial_discount_percentage
        else:
            self.commercial_discount_display = _('Commercial discount:')

    @api.one
    @api.depends('financial_discount_percentage')
    def _financial_discount_display(self):
        if self.financial_discount_percentage > 0:
            self.financial_discount_display = \
                _('Financial discount (%.2f %%) :')\
                %self.financial_discount_percentage
        else:
            self.financial_discount_display = _('Financial discount:')

    @api.one
    @api.constrains('commercial_discount_input')
    def _check_commercial_discount_percentage(self):
        if self.commercial_discount_input and \
            (self.commercial_discount_input < 0 or \
            self.commercial_discount_input > 100):
            raise Warning(_('Discount value should be between 0 and 100'))

    @api.one
    @api.constrains('financial_discount_input')
    def _check_financial_discount_percentage(self):
        if self.financial_discount_input and \
            (self.financial_discount_input < 0 or \
            self.financial_discount_input > 100):
            raise Warning(_('Discount value should be between 0 and 100'))

    def _get_lines_by_taxes(self, lines=None):
        """ This method will return a dictionary of taxes as keys
        with the related lines.
        """
        if lines is None:
            lines = self.order_line
        res = {}
        for line in lines:
            taxes = [tax.id for tax in line.tax_id]
            if taxes:
                taxes.sort()
            taxes_str = str(taxes)
            res.setdefault(taxes_str, [])
            res[taxes_str].append(line)
        return res

    @api.one
    def _generate_discounts_lines_by_taxes(self, lines_by_taxes):
        line_obj = self.env['sale.order.line']
        product_com = self.env.ref(
            'commercial_and_financial_discount.product_commercial_discount')
        product_fin = self.env.ref(
            'commercial_and_financial_discount.product_financial_discount')
        for tax_str in lines_by_taxes.keys():
            # Apply discounts percentages
            discount_com = self.commercial_discount_percentage / 100
            discount_fin = self.financial_discount_percentage / 100
            # Accumulate lines amounts
            sum = 0
            for line in lines_by_taxes[tax_str]:
                sum += line.price_subtotal
            # Calculate discounts amounts
            amount_com = sum * discount_com
            amount_fin = (sum - amount_com) * discount_fin
            # Add new lines with products of discounts
            for product_id, discount, is_com_disc, is_fin_disc, percentage in [
                        (product_com, amount_com, True, False, discount_com),
                        (product_fin, amount_fin, False, True, discount_fin)]:
                res = line_obj.product_id_change(
                    pricelist=self.pricelist_id.id,
                    product=product_id.id, qty=1,
                     partner_id=self.partner_id.id,
                    lang=self.partner_id.lang, update_tax=True,
                    date_order=self.date_order,
                    fiscal_position=self.fiscal_position.id)
                value = res.get('value')
                if value:
                    tax_ids = eval(tax_str)
                    description = product_id.name +\
                                  ' (%.2f %%)'%(percentage * 100)
                    value.update({
                        'name': description,
                        'commercial_discount': is_com_disc,
                        'financial_discount': is_fin_disc,
                        'price_unit': -discount,
                        'order_id': self.id,
                        'product_id': product_id.id,
                        'product_uom_qty': 1,
                        'product_uos_qty': 1,
                        'tax_id': [(6, 0, tax_ids)],
                    })
                    line_obj.create(value)

    @api.one
    def generate_discounts(self):
        if self.state in ('draft', 'sent'):
            # Delete previous discounts lines
            for line in self.order_line:
                if line.commercial_discount or line.financial_discount:
                    line.unlink()
            # Pass discounts to apply
            self.commercial_discount_percentage = self.commercial_discount_input
            self.financial_discount_percentage = self.financial_discount_input
            # Groups order lines by taxes types
            lines_by_taxes = self._get_lines_by_taxes()
            # Generate discounts lines by each tax and discount type
            if (len(lines_by_taxes) > 0) and \
                    (self.commercial_discount_percentage +
                     self.financial_discount_percentage > 0):
                self._generate_discounts_lines_by_taxes(lines_by_taxes)
            # Recompute amounts
            self._calculate_amounts
        return True

    @api.one
    def update_with_discounts(self):
        if self.state in ('draft', 'sent'):
            if self.commercial_discount_percentage or \
                    self.financial_discount_percentage:
               self.generate_discounts()
            else:
                # Delete old discounts lines
                for line in self.order_line:
                    if line.commercial_discount or line.financial_discount:
                        line.unlink()
                # Recompute amounts
                self._calculate_amounts
        return True