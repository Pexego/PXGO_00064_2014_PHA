# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
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
from openerp import models, api
from datetime import date, timedelta


class ProductStockByDay(models.TransientModel):
    _name = 'product.stock.by.day'

    @api.multi
    def compute_stock_by_day(self):
        # Clear first all calculations
        self.env['product.product'].search([]).\
            write({'stock_by_day': 0, 'bom_is_member_of': False})

        # Mark all products that is part of any BoM
        self.env['mrp.bom.line'].search([('product_id.type', '=', 'product')])\
            .mapped('product_id').write({'bom_is_member_of': True})

        last_365_days = (date.today() + timedelta(days=-365)).strftime('%Y-%m-%d')
        # Storable and saleable products, invoiced quantities in last year
        aiLines = self.env['account.invoice.line'].search([
            ('product_id.type', '=', 'product'),
            ('product_id.sale_ok', '=', True),
            ('invoice_id.date_invoice', '>=', last_365_days),
            ('invoice_id.type', 'in', ('out_invoice', 'out_refund')),
            ('invoice_id.state', 'in', ('open', 'paid'))
        ], order='product_id')
        if aiLines:
            product_id = aiLines[0].product_id
            invoiced_qty = 0
            for aiLine in aiLines:
                if product_id <> aiLine.product_id:
                    if invoiced_qty > 0:
                        product_id.stock_by_day = product_id.virtual_available /\
                                                  (invoiced_qty / 365)
                    else:
                        product_id.stock_by_day = 0
                    # Next product
                    product_id = aiLine.product_id
                    invoiced_qty = 0

                if aiLine.invoice_id.type == 'out_invoice':
                    invoiced_qty += aiLine.quantity
                else:
                    invoiced_qty -= aiLine.quantity

            # Save sum for last product in loop
            if invoiced_qty > 0:
                product_id.stock_by_day = product_id.virtual_available / \
                                          (invoiced_qty / 365)
            else:
                product_id.stock_by_day = 0

        # Storable but not saleable products
        lines = self.env['mrp.bom.line'].search([
                    ('product_id.type', '=', 'product'),
                    ('product_id.sale_ok', '=', False)
                ], order='product_id')
        if lines:
            product_id = lines[0].product_id
            sbd = lines[0].bom_id.product_id.stock_by_day
            for line in lines:
                if line.product_id <> product_id:
                    product_id.stock_by_day = sbd

                    # Next product
                    product_id = line.product_id
                    sbd = line.bom_id.product_id.stock_by_day
                elif line.bom_id.product_id.stock_by_day < sbd:
                    sbd = line.bom_id.product_id.stock_by_day

            # Save sbd for last product in loop
            if product_id.stock_by_day > sbd:
                product_id.stock_by_day = sbd
