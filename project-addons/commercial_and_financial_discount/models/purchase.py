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
from openerp.exceptions import Warning


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    price_subtotal = fields.Float(
        'Subtotal',
        compute='_amount_line',
        digits_compute= dp.get_precision('Account'))
    gross_amount = fields.Float(
        'Gross amount',
        compute='_amount_line',
        digits_compute= dp.get_precision('Account'))
    discount_amount = fields.Float(
        'Discount amount',
        compute='_amount_line',
        digits_compute= dp.get_precision('Account'))
    discounted_amount = fields.Float(
        'Discounted amount',
        compute='_amount_line',
        digits_compute= dp.get_precision('Account'))
    commercial_discount = fields.Float(
        'Commercial discount (%)',
        digits_compute=dp.get_precision('Discount'),
        readonly=True,
        default=0.0)
    financial_discount = fields.Float('Financial discount (%)',
        digits_compute=dp.get_precision('Discount'),
        readonly=True,
        default=0.0)

    @api.model
    def _calc_line_base_price(self, line):
        res = super(PurchaseOrderLine, self)._calc_line_base_price(line)
        return res * (1 - (line.commercial_discount or 0.0) / 100.0) * \
                     (1 - (line.financial_discount or 0.0) / 100.0)

    @api.one
    @api.depends('product_qty',
                 'price_unit',
                 'discount',
                 'commercial_discount',
                 'financial_discount')
    def _amount_line(self):
        price = self._calc_line_base_price(self)
        qty = self._calc_line_quantity(self)
        taxes = self.taxes_id.compute_all(price, qty,
                                        self.product_id,
                                        self.order_id.partner_id, False)
        cur = self.order_id.pricelist_id.currency_id
        self.gross_amount = cur.round(self.price_unit * qty)
        self.discount_amount = cur.round(self.gross_amount - price * qty)
        self.discounted_amount = cur.round(self.gross_amount *
                                           (1 - (self.discount or 0.0) / 100.0))
        self.price_subtotal = cur.round(taxes['total'])


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

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
    amount_with_article_discount = fields.Float(
        'Amount with article discount',
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
        compute='_commercial_discount_display',
        default='Commercial discount')
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
        compute='_financial_discount_display',
        default='Financial discount')
    financial_discount_amount = fields.Float(
        digits_compute=dp.get_precision('Account'),
        compute='_calculate_amounts',
        store=True)

    @api.model
    def _prepare_inv_line(self, account_id, order_line):
        result = super(PurchaseOrder, self)._prepare_inv_line(
            account_id, order_line)
        result['commercial_discount'] = order_line.commercial_discount or 0.0
        result['financial_discount'] = order_line.financial_discount or 0.0
        return result

    @api.multi
    @api.onchange('partner_id')
    def onchange_partner_id(self, partner_id):
        res = super(PurchaseOrder, self).onchange_partner_id(partner_id)
        partner = self.env['res.partner'].browse(partner_id)
        res['value'].update({
            'commercial_discount_input': partner.commercial_discount,
            'financial_discount_input': partner.financial_discount
        })
        return res

    @api.one
    @api.depends('order_line',
                 'order_line.product_qty',
                 'order_line.price_unit',
                 'order_line.discount',
                 'commercial_discount_percentage',
                 'financial_discount_percentage')
    def _calculate_amounts(self):
        amount_gross = 0
        art_disc_amount = 0
        com_disc_amount = 0
        fin_disc_amount = 0
        for line in self.order_line:
            amount = line.product_qty * line.price_unit
            amount_gross += amount
            art_disc_amount += amount * line.discount / 100
            aux = amount * (1 - line.discount / 100)
            com_disc_amount += aux * line.commercial_discount / 100
            aux = aux * (1 - line.commercial_discount / 100)
            fin_disc_amount += aux * line.financial_discount / 100
        self.amount_gross_untaxed = amount_gross
        self.article_discount = art_disc_amount
        self.amount_with_article_discount = amount_gross - art_disc_amount
        self.commercial_discount_amount = com_disc_amount
        self.amount_net_untaxed = amount_gross - art_disc_amount - \
                                  com_disc_amount
        self.financial_discount_amount = fin_disc_amount

    @api.model
    def _amount_line_tax(self, line):
        val = 0.0
        discounts = (1-(line.discount or 0.0)/100.0) * \
                    (1-(line.commercial_discount or 0.0)/100.0) * \
                    (1-(line.financial_discount or 0.0)/100.0)
        for c in line.taxes_id.compute_all(line.price_unit * discounts,
                 line.product_qty, line.product_id,
                 line.order_id.partner_id)['taxes']:
            val += c.get('amount', 0.0)
        return val

    @api.one
    @api.depends('commercial_discount_percentage')
    def _commercial_discount_display(self):
        if self.commercial_discount_percentage > 0:
            self.commercial_discount_display = \
                _('Commercial discount (%.2f %%)')\
                %self.commercial_discount_percentage
        else:
            self.commercial_discount_display = _('Commercial discount')

    @api.one
    @api.depends('financial_discount_percentage')
    def _financial_discount_display(self):
        if self.financial_discount_percentage > 0:
            self.financial_discount_display = \
                _('Financial discount (%.2f %%)')\
                %self.financial_discount_percentage
        else:
            self.financial_discount_display = _('Financial discount')

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

    @api.one
    def update_with_discounts(self):
        if self.state in ('draft', 'sent'):
            # Force to recompute amounts
            for line in self.order_line:
                line.commercial_discount = self.commercial_discount_percentage
                line.financial_discount = self.financial_discount_percentage
                # Fire write event on this field to activate _amount_all
                # function which recompute purchase totals
                line.price_unit = line.price_unit
        return True

    @api.one
    def generate_discounts(self):
        if self.state in ('draft', 'sent'):
            # Apply discounts per line
            for line in self.order_line:
                line.commercial_discount = self.commercial_discount_input
                line.financial_discount = self.financial_discount_input
                # Fire write event on this field to activate _amount_all
                # function which recompute purchase totals
                line.price_unit = line.price_unit
            # Save discounts applied
            self.commercial_discount_percentage = self.commercial_discount_input
            self.financial_discount_percentage = self.financial_discount_input
        return True
