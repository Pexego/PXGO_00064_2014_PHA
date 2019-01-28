# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api
from datetime import date, timedelta
import logging


class ProductStockByDay(models.TransientModel):
    _name = 'product.stock.by.day'

    data = {}
    bom_member_of_ids = False
    bom_line_dict = {}

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

        # Years back to compute
        years_back = 2
        start_date = (date.today() + timedelta(days=-(365 * years_back))).\
            strftime('%Y-%m-%d')

        # Closures to avoid code repetition
        def sbd_formula(cbd, vc):  # Consumption by day, virtual conservative stock
            if vc > 0:
                return (vc / cbd) if cbd > 0 else FLAG
            elif vc < 0:
                return -FLAG if cbd == 0 else (vc / cbd) * (1 if cbd > 0 else -1)
            else:
                return 0

        def save_sbd_and_cbd_i():
            cons_by_day_i = invoiced_qty / (365 * years_back)
            stock_by_day_i = sbd_formula(cons_by_day_i,
                                         product_id.virtual_conservative)
            if not self.data.has_key(product_id.id):
                self.data[product_id.id] = empty_dict.copy()
            self.data[product_id.id]['stock_by_day_i'] = stock_by_day_i
            self.data[product_id.id]['cons_by_day_i'] = cons_by_day_i

        def save_sbd_and_cbd_p():
            cons_by_day_p = moved_qty / (365 * years_back)
            stock_by_day_p = sbd_formula(cons_by_day_p,
                                         product_id.virtual_conservative)
            if not self.data.has_key(product_id.id):
                self.data[product_id.id] = empty_dict.copy()
            self.data[product_id.id]['stock_by_day_p'] = stock_by_day_p
            self.data[product_id.id]['cons_by_day_p'] = cons_by_day_p

        def compute_indirect_consumption(product_id):
            bom_line_dict_list = []
            for key, value in self.bom_line_dict.items():
                if value['product_id'] == product_id:
                    bom_line_dict_list.append(self.bom_line_dict.pop(key))

            for bom_line in bom_line_dict_list:
                # If final product of BoM is yet to be calculated, do it before
                if bom_line['final_product_id'] in self.bom_member_of_ids:
                    compute_indirect_consumption(bom_line['final_product_id'])

                fp = bom_line['final_product_id'].id  # Final product
                c = product_id.id  # Component of BoM
                if self.data.has_key(fp):
                    qty = bom_line['product_qty']
                    if not self.data.has_key(c):
                        self.data[c] = empty_dict.copy()
                    self.data[c]['cons_by_day_i_ind'] += \
                        self.data[fp]['cons_by_day_i'] * qty
                    self.data[c]['cons_by_day_p_ind'] += \
                        self.data[fp]['cons_by_day_p'] * qty
                    if self.data[fp]['stock_by_day_p'] < \
                            self.data[c]['stock_by_day_p_ind_min']:
                        self.data[c]['stock_by_day_p_ind_min'] = \
                            self.data[fp]['stock_by_day_p']
                self.bom_member_of_ids -= product_id

        # Products invoiced quantities in last year
        logger.info('Stock by Day: Computing stock by day based on invoices...')

        ai_lines = self.env['account.invoice.line'].search([
            ('product_id.active', '=', True),
            ('product_id.type', '=', 'product'),
            ('invoice_id.date_invoice', '>=', start_date),
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

                if ail.invoice_id.type == 'out_invoice':
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
            ('date', '>=', start_date),
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

                if sm.location_id.usage in ('internal', 'view', 'production',
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

        # Get all active BoM lines and products that are members of any BoM
        bom_line_ids = self.env['mrp.bom.line'].search([
            ('product_id.active', '=', True),
            ('bom_id.active', '=', True),
            ('bom_id.product_id.active', '=', True),
            ('bom_id.sequence', '<', 100)
        ], order='product_id')
        self.bom_member_of_ids = bom_line_ids.mapped('product_id')
        # Iterating dictionaries are much faster than model recursive searching
        for bom_line_id in bom_line_ids:
            self.bom_line_dict[bom_line_id.id] = {
                'product_id': bom_line_id.product_id,
                'final_product_id': bom_line_id.bom_id.product_id,
                'product_qty': bom_line_id.product_qty
            }
        del bom_line_ids  # Free resources

        while self.bom_member_of_ids:
            compute_indirect_consumption(self.bom_member_of_ids[0])

        # Now, iterate dictionary to do final calculations and
        # write computed data back to database
        logger.info('Stock by Day: Doing final calculations and writing data '
                    'back to %d products' % (len(self.data)))

        products = self.env['product.product']
        product_stock_unsafety = self.env['product.stock.unsafety']
        aIdx = [
            {'sbd': 'stock_by_day_i_ind',   'cbd': 'cons_by_day_i_ind'},
            {'sbd': 'stock_by_day_p_ind',   'cbd': 'cons_by_day_p_ind'},
            {'sbd': 'stock_by_day_i_total', 'cbd': 'cons_by_day_i_total'},
            {'sbd': 'stock_by_day_p_total', 'cbd': 'cons_by_day_p_total'}
        ]
        for id, values in self.data.iteritems():
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
            ('id', 'not in', self.data.keys())
        ]).with_context(disable_notify_changes=True).write(empty_dict)

        product_stock_unsafety.search([
            ('product_id.type', '=', 'product'),
            ('state', '!=', 'cancelled'),
            ('product_id.id', 'not in', self.data.keys())
        ]).write({
            'stock_by_day_i': FLAG,
            'stock_by_day_p': FLAG,
            'stock_by_day_p_ind_min': FLAG,
            'stock_by_day_i_total': 0,
            'stock_by_day_p_total': 0
        })

        logger.info('Stock by Day: All done!')
        return {'type': 'ir.actions.act_window_close'}