# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api
from datetime import date, timedelta
import logging


class ProductStockByDay(models.TransientModel):
    _name = 'product.stock.by.day'

    @api.multi
    def compute_stock_by_day(self):
        FLAG = 9999999.99  # Flag to detect unaltered data
        logger = logging.getLogger(__name__)

        data = {}
        bom_data = {}
        bom_line_dict = {}
        bom_member_of_ids = []

        empty_dict = {
#            'stock_by_day_i': FLAG,
#            'stock_by_day_p': FLAG,
            'cons_by_day_i': 0,
            'cons_by_day_p': 0,
#            'stock_by_day_i_ind': 0,
#            'stock_by_day_p_ind': 0,
#            'stock_by_day_p_ind_min': FLAG,
            'cons_by_day_i_ind': 0,
            'cons_by_day_p_ind': 0,
#            'stock_by_day_i_total': 0,
            'stock_by_day_p_total': 0,
            'cons_by_day_i_total': 0,
            'cons_by_day_p_total': 0
        }

        # Dates of periods to compute
        half_year_ago = (date.today() + timedelta(days=-183)).\
            strftime('%Y-%m-%d')
        a_year_ago = (date.today() + timedelta(days=-365)).\
            strftime('%Y-%m-%d')

        current_datetime = fields.datetime.now()

        # Closures to avoid code repetition
        def sbd_formula(cbd, vc):  # Consumption by day, virtual conservative stock
            if vc > 0:
                return (vc / cbd) if cbd > 0 else FLAG
            elif vc < 0:
                return -FLAG if cbd == 0 else (vc / cbd) * (1 if cbd > 0 else -1)
            else:
                return 0

        def save_sbd_and_cbd_i():
            days_passed = (current_datetime - date_first_invoice).days
            cons_by_day_i = invoiced_qty / days_passed if days_passed else 1
            cons_by_day_i *= sales_ratio
#            stock_by_day_i = sbd_formula(cons_by_day_i, virtual_conservative)
            if not data.has_key(product_id):
                data[product_id] = empty_dict.copy()
#            data[product_id]['stock_by_day_i'] = stock_by_day_i
            data[product_id]['cons_by_day_i'] = cons_by_day_i

        def save_sbd_and_cbd_p():
            days_passed = (current_datetime - date_first_move).days
            cons_by_day_p = moved_qty / days_passed if days_passed else 1
            cons_by_day_p *= sales_ratio
#            stock_by_day_p = sbd_formula(cons_by_day_p, virtual_conservative)
            if not data.has_key(product_id):
                data[product_id] = empty_dict.copy()
#            data[product_id]['stock_by_day_p'] = stock_by_day_p
            data[product_id]['cons_by_day_p'] = cons_by_day_p

        def add_consumption_based_on_bom(fp, c, c_bom_qty):
            # Direct final product consumption
            data[c]['cons_by_day_i_ind'] += \
                data[fp]['cons_by_day_i'] * c_bom_qty
            data[c]['cons_by_day_p_ind'] += \
                data[fp]['cons_by_day_p'] * c_bom_qty
 #           if data[fp]['stock_by_day_p'] < \
 #                   data[c]['stock_by_day_p_ind_min']:
 #               data[c]['stock_by_day_p_ind_min'] = \
 #                   data[fp]['stock_by_day_p']
            bom_data[c]['final_product_ids'] += [fp]
            bom_data[c]['final_product_qties'] += [c_bom_qty]

            # Indirect final products consumptions
            if not bom_data.has_key(fp):
                return True
            for idx, ind_fp in enumerate(bom_data[fp]['final_product_ids']):
                if ind_fp not in bom_data[c]['final_product_ids']:
                    ind_fp_bom_qty = bom_data[fp]['final_product_qties'][idx]
                    inherited_bom_qty = c_bom_qty * ind_fp_bom_qty
                    add_consumption_based_on_bom(ind_fp, c, inherited_bom_qty)

        def compute_indirect_consumption(product_id):
            bom_line_dict_list = []
            for key, value in bom_line_dict.items():
                if value['product_id'] == product_id:
                    bom_line_dict_list.append(bom_line_dict.pop(key))

            # Data dictionaries for this product
            if not data.has_key(product_id):
                data[product_id] = empty_dict.copy()
            if not bom_data.has_key(product_id):
                bom_data[product_id] = {
                    'final_product_ids': [],
                    'final_product_qties': []
                }

            for bom_line in bom_line_dict_list:
                # Final product of current BoM
                fp = bom_line['final_product_id']
                # If final product of BoM is yet to be calculated, do it before
                if fp in bom_member_of_ids:
                    compute_indirect_consumption(fp)
                # Consumption inherited from final product of the BoM
                if data.has_key(fp):
                    prod_bom_qty = bom_line['product_qty']
                    add_consumption_based_on_bom(fp, product_id, prod_bom_qty)

            if product_id in bom_member_of_ids:
                bom_member_of_ids.remove(product_id)

        # Products invoiced quantities in last two years
        logger.info('Stock by Day: Computing stock by day based on invoices...')

        sql = """
            select
                pp.id,
                pt.virtual_conservative,
                ai.date_invoice,
                ai.type,
                ail.quantity,
                pt.cons_by_day_ratio
            from account_invoice ai
            join account_invoice_line ail on ail.invoice_id = ai.id
            join product_product pp on pp.id = ail.product_id and pp.active {2} {3}
            join product_template pt on pt.id = pp.product_tmpl_id and pt.type = 'product'
            where ai.company_id = {0}
              and ai.date_invoice >= '{1}'
              and ai.type in ('out_invoice', 'out_refund')
              and ai.state in ('open', 'paid')
            order by pp.id, ai.date_invoice;        
        """
        # Fetch all products invoiced in last six months
        select_sql = sql.format(
            self.env.user.company_id.id,
            half_year_ago,
            '',
            ''
        )
        self.env.cr.execute(select_sql)
        ai_lines_data = self.env.cr.fetchall()
        # Fetch all products invoiced int the last year and have invoices
        # in the last six months
        select_sql = sql.format(
            self.env.user.company_id.id,
            a_year_ago,
            'and pp.id in ',
            tuple(set([d[0] for d in ai_lines_data]))  # Set to remove dupes
        )
        self.env.cr.execute(select_sql)
        ai_lines_data = self.env.cr.fetchall()
        if ai_lines_data:
            product_id = ai_lines_data[0][0]
            virtual_conservative = ai_lines_data[0][1]
            date_first_invoice = fields.Datetime.from_string(ai_lines_data[0][2])
            sales_ratio = ai_lines_data[0][5]
            invoiced_qty = 0
            for ail in ai_lines_data:
                if product_id <> ail[0]:
                    save_sbd_and_cbd_i()
                    product_id = ail[0]  # Next product
                    virtual_conservative = ail[1]
                    date_first_invoice = fields.Datetime.from_string(ail[2])
                    sales_ratio = ail[5]
                    invoiced_qty = 0

                invoiced_qty += ail[4] * 1 if ail[3] == 'out_invoice' else -1

            # Save sum for last product in loop
            save_sbd_and_cbd_i()
        del ai_lines_data  # Free resources

        # Products moved quantities in last two years
        logger.info('Stock by Day: Computing stock by day based on pickings...')

        sql = """
            select
                pp.id,
                pt.virtual_conservative,
                sm.date,
                case when (
                  sl.usage = 'internal'
                  and
                  (sld.usage = 'customer' or sld.id = 38)  -- Internal consumption
                ) then 'out'
                else 'in' end,
                sm.product_uom_qty,
                pt.cons_by_day_ratio
            from stock_move sm
            join product_product pp on pp.id = sm.product_id and pp.active {2} {3}
            join product_template pt on pt.id = pp.product_tmpl_id and pt.type = 'product'
            join stock_location sl on sl.id = sm.location_id
            join stock_location sld on sld.id = sm.location_dest_id
            where sm.company_id = {0}
              and sm.date >= '{1}'
              and sm.state = 'done'
              and ((
                  sl.usage = 'internal'
                  and
                  (sld.usage = 'customer' or sld.id = 38)  -- Internal consumption
                )	or (
                  (sl.usage = 'customer' or sl.id = 38)  -- Internal consumption
                  and
                  sld.usage = 'internal'
              ))
            order by pp.id, sm.date;       
        """
        # Fetch all products moved in last six months
        select_sql = sql.format(
            self.env.user.company_id.id,
            half_year_ago,
            '',
            ''
        )
        self.env.cr.execute(select_sql)
        moves_data = self.env.cr.fetchall()
        # Fetch all products moved in the las year and have moves in
        # the last six months
        select_sql = sql.format(
            self.env.user.company_id.id,
            a_year_ago,
            'and pp.id in',
            tuple(set([d[0] for d in moves_data]))  # Set to remove dupes
        )
        self.env.cr.execute(select_sql)
        moves_data = self.env.cr.fetchall()
        if moves_data:
            product_id = moves_data[0][0]
            virtual_conservative = moves_data[0][1]
            date_first_move = fields.Datetime.from_string(moves_data[0][2])
            sales_ratio = moves_data[0][5]
            moved_qty = 0
            for sm in moves_data:
                if product_id <> sm[0]:
                    save_sbd_and_cbd_p()
                    product_id = sm[0]  # Next product
                    virtual_conservative = sm[1]
                    date_first_move = fields.Datetime.from_string(sm[2])
                    sales_ratio = sm[5]
                    moved_qty = 0

                moved_qty += sm[4] * 1 if sm[3] == 'out' else -1

            # Save sum for last product in loop
            save_sbd_and_cbd_p()
        del moves_data  # Free resources

        # Products that are members of any bill of materials
        logger.info('Stock by Day: Computing indirect stock by day of BoM '
                    'members...')

        # Get all active BoM lines and products that are members of any BoM
        select_sql = """
            select
              row_number() over (order by ppl.id, pp.id) "id",
              ppl.id "product_id",
              pp.id "final_product_id",
              sum(mbl.product_qty) "product_qty"
            from mrp_bom_line mbl
            join product_product ppl on ppl.id = mbl.product_id and ppl.active
            join mrp_bom mb on mb.id = mbl.bom_id and mb.active
            join product_product pp on pp.id = mb.product_id and pp.active
            where mb.sequence < 100
              and mb.sequence = (
                select min(mb_aux.sequence)
                from mrp_bom mb_aux
                where mb_aux.product_id = mb.product_id
                  and mb_aux.active
            )
            group by ppl.id, pp.id, mbl.id;
        """
        self.env.cr.execute(select_sql)
        mbl_data = self.env.cr.fetchall()

        # Iterating dictionaries are much faster than model recursive searching
        for bl in mbl_data:
            bom_member_of_ids.append(bl[1])
            bom_line_dict[bl[0]] = {
                'product_id': bl[1],
                'final_product_id': bl[2],
                'product_qty': bl[3]
            }
        del mbl_data  # Free resources

        while bom_member_of_ids:
            compute_indirect_consumption(bom_member_of_ids[0])

        # Now, iterate dictionary to do final calculations and
        # write computed data back to database
        logger.info('Stock by Day: Doing final calculations and writing data '
                    'back to %d products' % (len(data)))

        a_idx = [
#            {'sbd': 'stock_by_day_i_ind',   'cbd': 'cons_by_day_i_ind'},
#            {'sbd': 'stock_by_day_p_ind',   'cbd': 'cons_by_day_p_ind'},
#            {'sbd': 'stock_by_day_i_total', 'cbd': 'cons_by_day_i_total'},
            {'sbd': 'stock_by_day_p_total', 'cbd': 'cons_by_day_p_total'}
        ]
        product_ids = self.env['product.product'].browse(data.keys())
        product_stock_unsafety_ids = self.env['product.stock.unsafety'].search([
            ('product_id', 'in', data.keys()),
            ('state', '!=', 'cancelled')
        ])
        for id, values in data.iteritems():
            product_id = product_ids.filtered(lambda p: p.id == id)
            values['cons_by_day_i_total'] = values['cons_by_day_i'] + \
                                            values['cons_by_day_i_ind']
            values['cons_by_day_p_total'] = values['cons_by_day_p'] + \
                                            values['cons_by_day_p_ind']

            for idx in a_idx:
                values[idx['sbd']] = sbd_formula(values[idx['cbd']],
                                                 product_id.virtual_conservative)

            product_id.with_context(disable_notify_changes=True).\
                write(values)  # Save calculations to database without notify

            psu = product_stock_unsafety_ids.filtered(lambda p: p.id == id)
            if psu:
                psu.write({
#                    'stock_by_day_i': values['stock_by_day_i'],
#                    'stock_by_day_p': values['stock_by_day_p'],
#                    'stock_by_day_p_ind_min': values['stock_by_day_p_ind_min'],
#                    'stock_by_day_i_total': values['stock_by_day_i_total'],
                    'stock_by_day_p_total': values['stock_by_day_p_total']
                })
        # Free resources
        del product_ids
        del product_stock_unsafety_ids

        # Clear all calculations on the rest of storable products
        logger.info('Stock by day: Cleaning old calculations on the rest of '
                    'products...')

        self.env['product.product'].search([
            ('type', '=', 'product'),
            ('id', 'not in', data.keys())
        ]).with_context(disable_notify_changes=True).write(empty_dict)

        self.env['product.stock.unsafety'].search([
            ('product_id.type', '=', 'product'),
            ('state', '!=', 'cancelled'),
            ('product_id.id', 'not in', data.keys())
        ]).write({
#            'stock_by_day_i': FLAG,
#            'stock_by_day_p': FLAG,
#            'stock_by_day_p_ind_min': FLAG,
#            'stock_by_day_i_total': 0,
            'stock_by_day_p_total': 0
        })

        logger.info('Stock by Day: All done!')
        return {'type': 'ir.actions.act_window_close'}