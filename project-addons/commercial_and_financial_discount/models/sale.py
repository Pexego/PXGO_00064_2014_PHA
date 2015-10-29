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
                      (line.product_uom_qty * line.price_unit * line.discount / 100)
        self.amount_gross_untaxed = amount_gross
        self.article_discount = discount_art
        self.commercial_discount_amount = com_disc_amount
        self.amount_net_untaxed = amount_gross - discount_art - \
                                  self.commercial_discount_amount
        self.financial_discount_amount = fin_disc_amount

    @api.one
    @api.depends('commercial_discount_percentage')
    def _commercial_discount_display(self):
        self.commercial_discount_display = _('Commercial discount') +\
                                          ' (%.2f %%) :'\
                                          %self.commercial_discount_percentage

    @api.one
    @api.depends('financial_discount_percentage')
    def _financial_discount_display(self):
        self.financial_discount_display = _('Financial discount') +\
                                          ' (%.2f %%) :'\
                                          %self.financial_discount_percentage
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
    @api.model
    def generate_discounts(self):
        line_obj = self.env['sale.order.line']
        product_com = self.env.ref(
            'commercial_and_financial_discount.product_commercial_discount')
        product_fin = self.env.ref(
            'commercial_and_financial_discount.product_financial_discount')
        if self.state in ('draft', 'sent'):
            # Apply percentages
            self.commercial_discount_percentage = self.commercial_discount_input
            self.financial_discount_percentage = self.financial_discount_input
            discount_fin = self.financial_discount_percentage / 100
            discount_com = self.commercial_discount_percentage / 100
            tot = 0
            for line in self.order_line:
                if line.commercial_discount or line.financial_discount:
                    line.unlink()
                else:
                    qty = line.product_uom_qty
                    pu = line.price_unit
                    sub = qty * pu
                    tot += sub
            discount_com = tot * discount_com
            if discount_com > 0:
                discount_fin = (tot - discount_com) * discount_fin
            else:
                discount_fin = tot * discount_fin
            for product_id, discount, is_com_disc, is_fin_disc in [
                                (product_com, discount_com, True, False),
                                (product_fin, discount_fin, False, True)]:
                res = line_obj.product_id_change(
                    pricelist=self.pricelist_id.id,
                    product=product_id.id, qty=1,
                    partner_id=self.partner_id.id,
                    lang=self.partner_id.lang, update_tax=True,
                    date_order=self.date_order,
                    fiscal_position=self.fiscal_position.id)
                value = res.get('value')
                if value:
                    tax_ids = value.get('tax_id') and \
                        [(6, 0, value.get('tax_id'))] or [(6, 0, [])]
                    value.update({
                        'commercial_discount': is_com_disc,
                        'financial_discount': is_fin_disc,
                        'price_unit': -discount,
                        'order_id': self.id,
                        'product_id': product_id.id,
                        'product_uom_qty': 1,
                        'product_uos_qty': 1,
                        'tax_id': tax_ids,
                    })
                    line_obj.create(value)
            # Recompute amounts
            self._calculate_amounts
        return True

