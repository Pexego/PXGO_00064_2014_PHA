# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api
from datetime import date, timedelta
import logging


class ProductStockByDay(models.TransientModel):
    _name = 'product.stock.by.day'

    @api.multi
    def compute_stock_by_day(self):
        FLAG = 9999999.99  # Flag to detect unaltered data
        logger = logging.getLogger(__name__)

        empty_dict = {
            'stock_by_day_i': FLAG,
            'stock_by_day_p': FLAG,
            'cons_by_day_i': 0,
            'cons_by_day_p': 0,
            'stock_by_day_i_ind': 0,
            'stock_by_day_p_ind': 0,
            'stock_by_day_p_ind_min': FLAG,
            'cons_by_day_i_ind': 0,
            'cons_by_day_p_ind': 0,
            'stock_by_day_i_total': 0,
            'stock_by_day_p_total': 0,
            'cons_by_day_i_total': 0,
            'cons_by_day_p_total': 0
        }

        # Compute a year ago date
        a_year_ago = (date.today() + timedelta(days=-365)).strftime('%Y-%m-%d')

        # Dictionary to minimize database writes
        data = {}

        # Closures to avoid code repetition
        def sbd_formula(cbd, vc):  # Consumption by day, virtual conservative stock
            if vc > 0:
                return (vc / cbd) if cbd > 0 else FLAG
            elif vc < 0:
                if cbd == 0:
                    return -FLAG
                else:
                    return (vc / cbd) * (1 if cbd > 0 else -1)
            else:
                return 0

        def save_sbd_and_cbd_i():
            cons_by_day_i = invoiced_qty / 365
            stock_by_day_i = sbd_formula(cons_by_day_i,
                                         product_id.virtual_conservative)
            if not data.has_key(product_id.id):
                data[product_id.id] = empty_dict.copy()
            data[product_id.id]['stock_by_day_i'] = stock_by_day_i
            data[product_id.id]['cons_by_day_i'] = cons_by_day_i

        def save_sbd_and_cbd_p():
            cons_by_day_p = moved_qty / 365
            stock_by_day_p = sbd_formula(cons_by_day_p,
                                         product_id.virtual_conservative)
            if not data.has_key(product_id.id):
                data[product_id.id] = empty_dict.copy()
            data[product_id.id]['stock_by_day_p'] = stock_by_day_p
            data[product_id.id]['cons_by_day_p'] = cons_by_day_p

        # Products invoiced quantities in last year
        logger.info('Stock by Day: Computing stock by day based on invoices...')

        ai_lines = self.env['account.invoice.line'].search([
            ('product_id.active', '=', True),
            ('product_id.type', '=', 'product'),
            ('invoice_id.date_invoice', '>=', a_year_ago),
            ('invoice_id.type', 'in', ('out_invoice', 'out_refund')),
            ('invoice_id.state', 'in', ('open', 'paid'))
        ], order='product_id')
        if ai_lines:
            product_id = ai_lines[0].product_id
            invoiced_qty = 0
            for ail in ai_lines:
                if product_id <> ail.product_id:
                    save_sbd_and_cbd_i()
                    product_id = ail.product_id  # Next product
                    invoiced_qty = 0
                elif ail.invoice_id.type == 'out_invoice':
                    invoiced_qty += ail.quantity
                else:
                    invoiced_qty -= ail.quantity

            # Save sum for last product in loop
            save_sbd_and_cbd_i()

        # Products moved quantities in last year
        logger.info('Stock by Day: Computing stock by day based on pickings...')

        sm_lines = self.env['stock.move'].search([
            ('product_id.active', '=', True),
            ('product_id.type', '=', 'product'),
            ('date', '>=', a_year_ago),
            ('state', '=', 'done'),
            '|',
            '&',
            ('location_id.usage', 'in', ('internal', 'view', 'production',
                                        'procurement', 'transit', 'supplier')),
            ('location_dest_id.usage', 'in', ('customer', 'inventory')),
            '&',
            ('location_dest_id.usage', 'in', ('internal', 'view', 'production',
                                         'procurement', 'transit', 'supplier')),
            ('location_id.usage', 'in', ('customer', 'inventory'))
        ], order='product_id')
        if sm_lines:
            product_id = sm_lines[0].product_id
            moved_qty = 0
            for sm in sm_lines:
                if product_id <> sm.product_id:
                    save_sbd_and_cbd_p()
                    product_id = sm.product_id  # Next product
                    moved_qty = 0
                elif sm.location_id.usage in ('internal', 'view', 'production',
                                     'procurement', 'transit', 'supplier') and \
                     sm.location_dest_id.usage in ('customer', 'inventory'):
                    moved_qty += sm.product_uom_qty
                elif sm.location_id.usage in ('customer', 'inventory') and \
                     sm.location_dest_id.usage in ('internal', 'view',
                            'production', 'procurement', 'transit', 'supplier'):
                    moved_qty -= sm.product_uom_qty

            # Save sum for last product in loop
            save_sbd_and_cbd_p()

        # Products that are members of any bill of materials
        logger.info('Stock by Day: Computing indirect stock by day of BoM '
                    'members...')

        bom_lines = self.env['mrp.bom.line'].search([
            ('product_id.active', '=', True),
            ('product_id.type', '=', 'product'),
            ('bom_id.active', '=', True),
            ('bom_id.product_id.active', '=', True)
        ], order='product_id')
        if bom_lines:
            for bom_line in bom_lines:
                fp = bom_line.bom_id.product_id.id  # Final product
                c = bom_line.product_id.id  # Component of BoM
                qty = bom_line.product_qty
                if data.has_key(fp):
                    if not data.has_key(c):
                        data[c] = empty_dict.copy()
                    data[c]['cons_by_day_i_ind'] += \
                        data[fp]['cons_by_day_i'] * qty
                    data[c]['cons_by_day_p_ind'] += \
                        data[fp]['cons_by_day_p'] * qty
                    if data[fp]['stock_by_day_p'] < \
                            data[c]['stock_by_day_p_ind_min']:
                        data[c]['stock_by_day_p_ind_min'] = \
                            data[fp]['stock_by_day_p']

        # Now, iterate dictionary to do final calculations and
        # write computed data back to database
        logger.info('Stock by Day: Doing final calculations and writing data '
                    'back to %d products' % (len(data)))

        products = self.env['product.product']
        product_stock_unsafety = self.env['product.stock.unsafety']
        aIdx = [
            {'sbd': 'stock_by_day_i_ind',   'cbd': 'cons_by_day_i_ind'},
            {'sbd': 'stock_by_day_p_ind',   'cbd': 'cons_by_day_p_ind'},
            {'sbd': 'stock_by_day_i_total', 'cbd': 'cons_by_day_i_total'},
            {'sbd': 'stock_by_day_p_total', 'cbd': 'cons_by_day_p_total'}
        ]
        for id, values in data.iteritems():
            product_id = products.browse(id)
            values['cons_by_day_i_total'] = values['cons_by_day_i'] + \
                                            values['cons_by_day_i_ind']
            values['cons_by_day_p_total'] = values['cons_by_day_p'] + \
                                            values['cons_by_day_p_ind']

            for idx in aIdx:
                values[idx['sbd']] = sbd_formula(values[idx['cbd']],
                                                 product_id.virtual_conservative)

            product_id.with_context(disable_notify_changes=True).\
                write(values)  # Save calculations to database without notify

            psu = product_stock_unsafety.search([
                ('product_id', '=', product_id.id),
                ('state', '!=', 'cancelled')
            ])
            if psu:
                psu.write({
                    'stock_by_day_i': values['stock_by_day_i'],
                    'stock_by_day_p': values['stock_by_day_p'],
                    'stock_by_day_p_ind_min': values['stock_by_day_p_ind_min'],
                    'stock_by_day_i_total': values['stock_by_day_i_total'],
                    'stock_by_day_p_total': values['stock_by_day_p_total']
                })

        # Clear all calculations on the rest of storable products
        logger.info('Stock by day: Cleaning old calculations on the rest of '
                    'products...')

        products.search([
            ('type', '=', 'product'),
            ('id', 'not in', data.keys())
        ]).with_context(disable_notify_changes=True).write(empty_dict)

        product_stock_unsafety.search([
            ('product_id.type', '=', 'product'),
            ('state', '!=', 'cancelled'),
            ('product_id.id', 'not in', data.keys())
        ]).write({
            'stock_by_day_i': FLAG,
            'stock_by_day_p': FLAG,
            'stock_by_day_p_ind_min': FLAG,
            'stock_by_day_i_total': 0,
            'stock_by_day_p_total': 0
        })

        logger.info('Stock by Day: All done!')
        return {'type': 'ir.actions.act_window_close'}