# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Julius Network Solutions SARL <contact@julius.fr>
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
#################################################################################

from openerp import models, api, fields

class StockPicking(models.Model):
    _inherit = 'stock.picking'

    def _generate_financial_discount_invoice_line(self, picking, invoice, sale_order_id):
        line_obj = self.env['sale.order.line']
        sale_order_obj = self.env['sale.order']
        value = {}
        sale_order = sale_order_obj.browse(sale_order_id)
        if sale_order.financial_discount_percentage != 0.00:
            discount = sale_order.financial_discount_percentage / 100
            res = 0
            for line in invoice.invoice_line:
                if line.financial_discount == False:
                    qty = line.quantity
                    pu = line.price_unit
                    sub = qty * pu
                    res += sub
            discount_value = res * discount
            product_id = self.env.ref(
                'comercial_and_financial_discount.product_financial_discount')
            res = line_obj.product_id_change([],
                pricelist=sale_order.pricelist_id.id,
                product=product_id, qty=1,
                partner_id=sale_order.partner_id.id,
                lang=sale_order.partner_id.lang, update_tax=True,
                date_order=sale_order.date_order,
                fiscal_position=sale_order.fiscal_position)
            value = res.get('value')
            if value:
                tax_ids = value.get('tax_id') and \
                    [(6, 0, value.get('tax_id'))] or [(6, 0, [])]
                value.update({
                    'invoice_id': invoice.id,
                    'product_id': product_id,
                    'price_unit': -discount_value,
                    'quantity': 1,
                    'invoice_line_tax_id': tax_ids,
                })
        return value

    def action_invoice_create(self, journal_id=False, group=False, type='out_invoice'):
        invoice_obj = self.env['account.invoice']
        picking_obj = self.env['stock.picking']
        invoice_line_obj = self.env['account.invoice.line']

        res = super(StockPicking, self).action_invoice_create(
            journal_id=False, group=False, type='out_invoice')

        for picking in picking_obj.browse(res.keys()):
            invoice = invoice_obj.browse(res[picking.id])
            sale_order_id = picking.sale_id and picking.sale_id.id or False
            invoice_line = self._generate_financial_discount_invoice_line(
                picking, invoice, sale_order_id)
            if invoice_line != {}:
                invoice_line_obj.create(invoice_line)
                invoice_obj.button_compute([invoice.id])

        return res
