# -*- coding: utf-8 -*-
###############################################################################
#
#    Copyright (c) 2009 Angel Alvarez - NaN  (http://www.nan-tic.com)
#    Copyright (C) 2012 Domsense srl (<http://www.domsense.com>)
#    Copyright (C) 2013 Agile Business Group sagl (<http://www.agilebg.com>)
#    Copyright (C) 2014 Pexego Sistemas Informáticos
#    Copyright (C) 2015 Óscar Salvador - Pharmadus (http://www.pharmadus.com)
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
###############################################################################

import math
from openerp.osv import fields, orm, osv
import openerp.addons.decimal_precision as dp
from openerp import api

class product_pack(orm.Model):
    _name = 'product.pack.line'
    _rec_name = 'product_id'
    _columns = {
        'parent_product_id': fields.many2one(
            'product.template', 'Parent Product',
            ondelete='cascade', required=True
        ),
        'quantity': fields.float('Quantity', required=True),
        'product_id': fields.many2one(
            'product.template', 'Product', required=True
        ),
    }


class product_product(orm.Model):
    _inherit = 'product.template'

    def _product_available(self, cr, uid, ids, field_names=None, arg=False, context=None):
        res = {}
        for product in self.browse(cr, uid, ids, context=context):
            stock = super(product_product, self)._product_available(
                cr, uid, [product.id], field_names, arg, context)

            if not product.stock_depends:
                res[product.id] = stock[product.id]
                continue

            first_subproduct = True
            pack_stock = 0

            # Check if product stock depends on it's subproducts stock.
            if product.pack_line_ids:
                """ Go over all subproducts, take quantity needed for the pack
                and its available stock """
                for subproduct in product.pack_line_ids:

                    # if subproduct is a service don't calculate the stock
                    if subproduct.product_id.type == 'service':
                        continue
                    if first_subproduct:
                        subproduct_quantity = subproduct.quantity
                        subproduct_stock = self._product_available(cr, uid, [subproduct.product_id.id], field_names, arg, context)[subproduct.product_id.id]['qty_available']
                        if subproduct_quantity == 0:
                            continue

                        """ Calculate real stock for current pack from the
                        subproduct stock and needed quantity """
                        pack_stock = math.floor(
                            subproduct_stock / subproduct_quantity)
                        first_subproduct = False
                        continue

                    # Take the info of the next subproduct
                    subproduct_quantity_next = subproduct.quantity
                    subproduct_stock_next = self._product_available(cr, uid, [subproduct.product_id.id], field_names, arg, context)[subproduct.product_id.id]['qty_available']

                    if (
                        subproduct_quantity_next == 0
                        or subproduct_quantity_next == 0.0
                    ):
                        continue

                    pack_stock_next = math.floor(
                        subproduct_stock_next / subproduct_quantity_next)

                    # compare the stock of a subproduct and the next subproduct
                    if pack_stock_next < pack_stock:
                        pack_stock = pack_stock_next

                # result is the minimum stock of all subproducts
                res[product.id] = {
                    'qty_available': pack_stock,
                    'incoming_qty': 0,
                    'outgoing_qty': 0,
                    'virtual_available': pack_stock,
                }
            else:
                res[product.id] = stock[product.id]
        return res

    def _search_product_quantity(self, cr, uid, obj, name, domain, context):
        return super(product_product, self)._search_product_quantity(cr, uid, obj, name, domain, context)

    _columns = {
        'stock_depends': fields.boolean(
            'Stock depends of components',
            help='Mark if pack stock is calcualted from component stock'
        ),
        'pack_fixed_price': fields.boolean(
            'Pack has fixed price',
            help="""
            Mark this field if the public price of the pack should be fixed.
            Do not mark it if the price should be calculated from the sum of
            the prices of the products in the pack.
        """
        ),
        'pack_line_ids': fields.one2many(
            'product.pack.line', 'parent_product_id', 'Pack Products',
            help='List of products that are part of this pack.'
        ),
        'qty_available': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Quantity On Hand',
            fnct_search=_search_product_quantity,
            help="Current quantity of products.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored at this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "stored in the Stock Location of the Warehouse of this Shop, "
                 "or any of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
        'virtual_available': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Forecast Quantity',
            fnct_search=_search_product_quantity,
            help="Forecast quantity (computed as Quantity On Hand "
                 "- Outgoing + Incoming)\n"
                 "In a context with a single Stock Location, this includes "
                 "goods stored in this location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods stored in the Stock Location of this Warehouse, or any "
                 "of its children.\n"
                 "Otherwise, this includes goods stored in any Stock Location "
                 "with 'internal' type."),
        'incoming_qty': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Incoming',
            fnct_search=_search_product_quantity,
            help="Quantity of products that are planned to arrive.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods arriving to this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods arriving to the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "Otherwise, this includes goods arriving to any Stock "
                 "Location with 'internal' type."),
        'outgoing_qty': fields.function(_product_available, multi='qty_available',
            type='float', digits_compute=dp.get_precision('Product Unit of Measure'),
            string='Outgoing',
            fnct_search=_search_product_quantity,
            help="Quantity of products that are planned to leave.\n"
                 "In a context with a single Stock Location, this includes "
                 "goods leaving this Location, or any of its children.\n"
                 "In a context with a single Warehouse, this includes "
                 "goods leaving the Stock Location of this Warehouse, or "
                 "any of its children.\n"
                 "Otherwise, this includes goods leaving any Stock "
                 "Location with 'internal' type."),
    }

    _defaults = {
        'pack_fixed_price': True,
    }


class sale_order_line(orm.Model):
    _inherit = 'sale.order.line'

    def _pack_icon(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = 'terp-camera_test' if line.pack_parent_line_id else ''
        return res

    _columns = {
        'pack_depth': fields.integer(
            'Depth', required=True,
            help='Depth of the product if it is part of a pack.'
        ),
        'pack_parent_line_id': fields.many2one(
            'sale.order.line', 'Pack',
            help='The pack that contains this product.', ondelete="cascade"
        ),
        'pack_child_line_ids': fields.one2many(
            'sale.order.line', 'pack_parent_line_id', 'Lines in pack'),
        'pack_icon': fields.function(_pack_icon, string='Pack component', type='char', store=False),
    }
    _defaults = {
        'pack_depth': 0,
    }

    def invoice_line_create(self, cr, uid, ids, context=None):
        no_pack_ids = []
        for line in self.browse(cr, uid, ids, context):
            if not line.pack_depth > 0:
                no_pack_ids.append(line.id)
        return super(sale_order_line, self).invoice_line_create(cr, uid, no_pack_ids, context)

    @api.multi
    def pack_in_moves(self, product_ids):
        is_in_list = True
        for child in self.pack_child_line_ids:
            if child.pack_child_line_ids:
                if not child.pack_in_moves(product_ids):
                    is_in_list = False
            else:
                if child.product_id.id not in product_ids:
                    is_in_list = False
        return is_in_list


class sale_order(orm.Model):
    _inherit = 'sale.order'

    def create(self, cr, uid, vals, context=None):
        result = super(sale_order, self).create(cr, uid, vals, context)
        self.expand_packs(cr, uid, [result], context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        result = super(sale_order, self).write(cr, uid, ids, vals, context)
        self.expand_packs(cr, uid, ids, context)
        return result

    def copy(self, cr, uid, id, default={}, context=None):
        line_obj = self.pool.get('sale.order.line')
        result = super(sale_order, self).copy(cr, uid, id, default, context)
        sale = self.browse(cr, uid, result, context)
        self.unlink_pack_components(cr, uid, sale.id, context)
        self.expand_packs(cr, uid, sale.id, context)
        return result

    def unlink_pack_components(self, cr, uid, sale_id, context=None):
        unlink_lines = self.pool.get('sale.order.line').search(cr, uid, [('order_id', '=', sale_id), ('pack_parent_line_id', '!=', None), ('pack_child_line_ids', '=', None)], context=context)
        if unlink_lines:
            self.pool.get('sale.order.line').unlink(cr, uid, unlink_lines, context)
            self.unlink_pack_components(cr, uid, sale_id, context)
        else:
            return


    def expand_packs(self, cr, uid, ids, context={}, depth=1):
        if type(ids) in [int, long]:
            ids = [ids]
        if depth == 10:
            return
        updated_orders = []
        for order in self.browse(cr, uid, ids, context):

            fiscal_position = (
                order.fiscal_position
                and self.pool.get('account.fiscal.position').browse(
                    cr, uid, order.fiscal_position.id, context
                )
                or False
            )
            """
            The reorder variable is used to ensure lines of the same pack go
            right after their parent. What the algorithm does is check if the
            previous item had children. As children items must go right after
            the parent if the line we're evaluating doesn't have a parent it
            means it's a new item (and probably has the default 10 sequence
            number - unless the appropiate c2c_sale_sequence module is
            installed). In this case we mark the item for reordering and
            evaluate the next one. Note that as the item is not evaluated and
            it might have to be expanded it's put on the queue for another
            iteration (it's simple and works well). Once the next item has been
            evaluated the sequence of the item marked for reordering is updated
            with the next value.
            """
            sequence = -1
            reorder = []
            last_had_children = False
            for line in order.order_line:
                if last_had_children and not line.pack_parent_line_id:
                    reorder.append(line.id)
                    if (
                        line.product_id.pack_line_ids
                        and order.id not in updated_orders
                    ):
                        updated_orders.append(order.id)
                    continue

                sequence += 1

                if sequence > line.sequence:
                    self.pool.get('sale.order.line').write(
                        cr, uid, [line.id], {'sequence': sequence, }, context)
                else:
                    sequence = line.sequence

                if line.state != 'draft':
                    continue
                if not line.product_id:
                    continue

                """ If pack was already expanded (in another create/write
                operation or in a previous iteration) don't do it again. """
                if line.pack_child_line_ids:
                    last_had_children = True
                    continue
                last_had_children = False

                for subline in line.product_id.pack_line_ids:
                    sequence += 1

                    subproduct = subline.product_id
                    quantity = subline.quantity * line.product_uom_qty

                    if line.product_id.pack_fixed_price:
                        price = 0.0
                        discount = 0.0
                    else:
                        pricelist = order.pricelist_id.id
                        price = self.pool.get('product.pricelist').price_get(
                            cr, uid, [pricelist], subproduct.id, quantity,
                            order.partner_id.id, {
                                'uom': subproduct.uom_id.id,
                                'date': order.date_order,
                                }
                            )[pricelist]
                        discount = line.discount

                    # Obtain product name in partner's language
                    ctx = {'lang': order.partner_id.lang}
                    subproduct_name = self.pool.get('product.template').browse(
                        cr, uid, subproduct.id, ctx).name

                    tax_ids = self.pool.get('account.fiscal.position').map_tax(
                        cr, uid, fiscal_position, subproduct.taxes_id)

                    if subproduct.uos_id:
                        uos_id = subproduct.uos_id.id
                        uos_qty = quantity * subproduct.uos_coeff
                    else:
                        uos_id = False
                        uos_qty = quantity

                    vals = {
                        'order_id': order.id,
                        'name': '%s%s' % (
                            '>> ' * (line.pack_depth+1), subproduct_name
                        ),
                        'sequence': sequence,
                        'delay': subproduct.sale_delay or 0.0,
                        'product_id': subproduct.id,
                        'procurement_ids': (
                            [(4, x.id) for x in line.procurement_ids]
                        ),
                        'price_unit': price,
                        'tax_id': [(6, 0, tax_ids)],
                        'address_allotment_id': False,
                        'product_uom_qty': quantity,
                        'product_uom': subproduct.uom_id.id,
                        'product_uos_qty': uos_qty,
                        'product_uos': uos_id,
                        'product_packaging': False,
                        'discount': discount,
                        'number_packages': False,
                        'th_weight': False,
                        'state': 'draft',
                        'pack_parent_line_id': line.id,
                        'pack_depth': line.pack_depth + 1,
                    }

                    """ It's a control for the case that the
                    nan_external_prices was installed with the product pack """
                    if 'prices_used' in line:
                        vals['prices_used'] = line.prices_used

                    self.pool.get('sale.order.line').create(
                        cr, uid, vals, context)
                    if order.id not in updated_orders:
                        updated_orders.append(order.id)

                for id in reorder:
                    sequence += 1
                    self.pool.get('sale.order.line').write(
                        cr, uid, [id], {'sequence': sequence, }, context)

        if updated_orders:
            """ Try to expand again all those orders that had a pack in this
            iteration. This way we support packs inside other packs. """
            self.expand_packs(cr, uid, ids, context, depth + 1)
        return

class sale_report(osv.osv):
    _inherit = 'sale.report'

    def _group_by(self):
        group_by_str = super(sale_report, self)._group_by()
        return "WHERE l.pack_depth=0" + group_by_str



class purchase_order_line(orm.Model):
    _inherit = 'purchase.order.line'
    _columns = {
        'sequence': fields.integer(
            'Sequence',
            help="""Gives the sequence order when displaying a list of
            purchase order lines. """
        ),
        'pack_depth': fields.integer(
            'Depth', required=True,
            help='Depth of the product if it is part of a pack.'
        ),
        'pack_parent_line_id': fields.many2one(
            'purchase.order.line', 'Pack',
            help='The pack that contains this product.'
        ),
        'pack_child_line_ids': fields.one2many(
            'purchase.order.line', 'pack_parent_line_id', 'Lines in pack'
        ),
    }
    _defaults = {
        'pack_depth': 0,
    }


class purchase_order(orm.Model):
    _inherit = 'purchase.order'

    def create(self, cr, uid, vals, context=None):
        result = super(purchase_order, self).create(cr, uid, vals, context)
        self.expand_packs(cr, uid, [result], context)
        return result

    def write(self, cr, uid, ids, vals, context=None):
        result = super(purchase_order, self).write(cr, uid, ids, vals, context)
        self.expand_packs(cr, uid, ids, context)
        return result

    def expand_packs(self, cr, uid, ids, context={}, depth=1):
        if type(ids) in [int, long]:
            ids = [ids]
        if depth == 10:
            return
        updated_orders = []
        for order in self.browse(cr, uid, ids, context):
            fiscal_position = (
                order.fiscal_position
                and self.pool.get('account.fiscal.position').browse(
                    cr, uid, order.fiscal_position.id, context
                )
                or False
            )
            """
            The reorder variable is used to ensure lines of the same pack go
            right after their parent. What the algorithm does is check if the
            previous item had children. As children items must go right after
            the parent if the line we're evaluating doesn't have a parent it
            means it's a new item (and probably has the default 10 sequence
            number - unless the appropiate c2c_sale_sequence module is
            installed). In this case we mark the item for reordering and
            evaluate the next one. Note that as the item is not evaluated and
            it might have to be expanded it's put on the queue for another
            iteration (it's simple and works well). Once the next item has been
            evaluated the sequence of the item marked for reordering is updated
            with the next value.
            """
            sequence = -1
            reorder = []
            last_had_children = False
            for line in order.order_line:
                if last_had_children and not line.pack_parent_line_id:
                    reorder.append(line.id)
                    if (
                        line.product_id.pack_line_ids
                        and order.id not in updated_orders
                    ):
                        updated_orders.append(order.id)
                    continue

                sequence += 1

                if sequence > line.sequence:
                    self.pool.get('purchase.order.line').write(
                        cr, uid, [line.id], {'sequence': sequence, }, context)
                else:
                    sequence = line.sequence

                if line.state != 'draft':
                    continue
                if not line.product_id:
                    continue

                # If pack was already expanded (in another create/write
                # operation or in a previous iteration) don't do it again.
                if line.pack_child_line_ids:
                    last_had_children = True
                    continue
                last_had_children = False

                for subline in line.product_id.pack_line_ids:
                    sequence += 1

                    subproduct = subline.product_id
                    quantity = subline.quantity * line.product_qty

                    if line.product_id.pack_fixed_price:
                        price = 0.0
                    else:
                        pricelist = order.pricelist_id.id
                        price = self.pool.get('product.pricelist').price_get(
                            cr, uid, [pricelist], subproduct.id, quantity,
                            order.partner_id.id, {
                                'uom': subproduct.uom_id.id,
                                'date': order.date_order,
                                }
                            )[pricelist]

                    # Obtain product name in partner's language
                    ctx = {'lang': order.partner_id.lang}
                    subproduct_name = self.pool.get('product.template').browse(
                        cr, uid, subproduct.id, ctx).name

                    tax_ids = self.pool.get('account.fiscal.position').map_tax(
                        cr, uid, fiscal_position, subproduct.taxes_id)

                    vals = {
                        'order_id': order.id,
                        'name': '%s%s' % (
                            '> ' * (line.pack_depth + 1), subproduct_name),
                        'date_planned': line.date_planned or 0.0,
                        'sequence': sequence,
                        'product_id': subproduct.id,
                        'price_unit': price,
                        'taxes_id': [(6, 0, tax_ids)],
                        'product_qty': quantity,
                        'product_uom': subproduct.uom_id.id,
                        'move_ids': [(6, 0, [])],
                        'state': 'draft',
                        'pack_parent_line_id': line.id,
                        'pack_depth': line.pack_depth + 1,
                    }

                    # It's a control for the case that the nan_external_prices
                    # was installed with the product pack
                    if 'prices_used' in line:
                        vals['prices_used'] = line.prices_used

                    self.pool.get('purchase.order.line').create(
                        cr, uid, vals, context)
                    if order.id not in updated_orders:
                        updated_orders.append(order.id)

                for id in reorder:
                    sequence += 1
                    self.pool.get('purchase.order.line').write(
                        cr, uid, [id], {'sequence': sequence, }, context)

        if updated_orders:
            """ Try to expand again all those orders that had a pack in this
            iteration. This way we support packs inside other packs. """
            self.expand_packs(cr, uid, ids, context, depth + 1)
        return

    '''def action_invoice_create(self, cr, uid, ids, context=None):
        """Generates invoice for given ids of purchase orders and links that invoice ID to purchase order.
        :param ids: list of ids of purchase orders.
        :return: ID of created invoice.
        :rtype: int
        """
        context = dict(context or {})

        inv_obj = self.pool.get('account.invoice')
        inv_line_obj = self.pool.get('account.invoice.line')

        res = False
        uid_company_id = self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id
        for order in self.browse(cr, uid, ids, context=context):
            context.pop('force_company', None)
            if order.company_id.id != uid_company_id:
                #if the company of the document is different than the current user company, force the company in the context
                #then re-do a browse to read the property fields for the good company.
                context['force_company'] = order.company_id.id
                order = self.browse(cr, uid, order.id, context=context)

            # generate invoice line correspond to PO line and link that to created invoice (inv_id) and PO line
            inv_lines = []
            for po_line in order.order_line:
                if po_line.pack_depth > 0:
                    continue
                acc_id = self._choose_account_from_po_line(cr, uid, po_line, context=context)
                inv_line_data = self._prepare_inv_line(cr, uid, acc_id, po_line, context=context)
                inv_line_id = inv_line_obj.create(cr, uid, inv_line_data, context=context)
                inv_lines.append(inv_line_id)
                po_line.write({'invoice_lines': [(4, inv_line_id)]})

            # get invoice data and create invoice
            inv_data = self._prepare_invoice(cr, uid, order, inv_lines, context=context)
            inv_id = inv_obj.create(cr, uid, inv_data, context=context)

            # compute the invoice
            inv_obj.button_compute(cr, uid, [inv_id], context=context, set_total=True)

            # Link this new invoice to related purchase order
            order.write({'invoice_ids': [(4, inv_id)]})
            res = inv_id
        return res'''


class stock_picking(orm.Model):

    _inherit = 'stock.picking'

    def action_invoice_create(self, cr, uid, ids, journal_id, group=False, type='out_invoice', context=None):
        """ Creates invoice based on the invoice state selected for picking.
        @param journal_id: Id of journal
        @param group: Whether to create a group invoice or not
        @param type: Type invoice to be created
        @return: Ids of created invoices for the pickings
        """
        context = context or {}
        inv_line_obj = self.pool.get('account.invoice.line')
        todo = {}
        for picking in self.browse(cr, uid, ids, context=context):
            partner = self._get_partner_to_invoice(cr, uid, picking, context)
            #grouping is based on the invoiced partner
            if group:
                key = partner
            else:
                key = picking.id
            for move in picking.move_lines:
                if move.invoice_state == '2binvoiced':
                    if (move.state != 'cancel') and not move.scrapped:
                        todo.setdefault(key, [])
                        todo[key].append(move)
        invoices = []
        for moves in todo.values():
            final_moves = []
            pack_moves = []
            for move in moves:
                if not move.pack_component:
                    final_moves.append(move)
                else:
                    pack_moves.append(move)
            if final_moves:
                invoices += self._invoice_create_line(cr, uid, final_moves, journal_id, type, context=context)
            else:
                # Si el albarán no tiene ningun movimiento facturable se crea
                # una factura con uno de los movimientos y se borran las líneas.
                invoice = self._invoice_create_line(cr, uid, [moves[0]], journal_id, type, context=context)
                to_delete = inv_line_obj.search(cr, uid,
                    [('invoice_id', '=', invoice),
                     ('product_id', '=', moves[0].product_id.id)], context=context)
                inv_line_obj.unlink(cr, uid, to_delete, context)
                invoices += invoice
            if pack_moves:
                self.pool.get('stock.move').write(cr, uid, [x.id for x in pack_moves], {'invoice_state': 'invoiced'}, context)
        return invoices


    def _create_invoice_from_picking(self, cr, uid, picking, vals, context=None):
        sale_obj = self.pool.get('sale.order')
        sale_line_obj = self.pool.get('sale.order.line')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_id = super(stock_picking, self)._create_invoice_from_picking(cr, uid, picking, vals, context=context)
        picking_product_ids = [x.product_id.id for x in picking.move_lines]
        if picking.group_id:
            sale_ids = sale_obj.search(cr, uid, [('procurement_group_id', '=', picking.group_id.id)], context=context)
            if sale_ids:
                sale_line_ids = sale_line_obj.search(cr, uid, [('order_id', 'in', sale_ids), ('product_id.type', '=', 'service')], context=context)
                if sale_line_ids:
                    for line in sale_line_obj.browse(cr, uid, sale_line_ids, context):
                        if line.pack_child_line_ids and not line.pack_parent_line_id and line.invoiced:
                            if not line.pack_in_moves(picking_product_ids):
                                invoice_line_obj.unlink(cr, uid, [x.id for x in line.invoice_lines], context)
                                sale_line_obj.write(cr, uid, line.id, {'invoice_lines': False}, context)
        return invoice_id


class stock_move(orm.Model):

    _inherit = 'stock.move'

    @api.multi
    def get_sale_line_id(self):
        sale_id = self.procurement_id.sale_line_id
        if not sale_id and self.move_dest_id:
            sale_id = self.move_dest_id.get_sale_line_id()
        return sale_id

    def _pack_component(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for move in self.browse(cr, uid, ids, context):
            res[move.id] = False
            if self.get_sale_line_id(cr, uid, move.id, context):
                if self.get_sale_line_id(cr, uid, move.id, context).pack_parent_line_id:
                    res[move.id] = True
        return res

    def _pack_icon(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for line in self.browse(cr, uid, ids, context):
            res[line.id] = 'terp-camera_test' if line.pack_component else ''
        return res

    _columns = {
        'pack_component': fields.function(_pack_component,
                                          string='Pack component',
                                          type='boolean',
                                          store=False),
        'pack_icon': fields.function(_pack_icon, string='Pack component', type='char', store=False),
    }


class stock_pack_operation(orm.Model):

    _inherit = 'stock.pack.operation'

    def _pack_component(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for operation in self.browse(cr, uid, ids, context):
            res[operation.id] = False
            for move in operation.linked_move_operation_ids:
                if move.move_id.pack_component:
                    res[operation.id] = True
        return res

    _columns = {
        'pack_component': fields.function(_pack_component,
                                          string='pack component',
                                          type='boolean',
                                          store=True),
    }


class stock_return_picking(orm.TransientModel):
    _inherit = 'stock.return.picking'

    def _create_returns(self, cr, uid, ids, context=None):
        data = self.browse(cr, uid, ids[0], context=context)
        if data.invoice_state == '2binvoiced':
            sale_obj = self.pool.get('sale.order')
            sale_line_obj = self.pool.get('sale.order.line')
            record_id = context and context.get('active_id', False) or False
            picking = self.pool.get('stock.picking').browse(cr, uid, record_id,
                                                            context)
            picking_product_ids = [x.product_id.id for x in picking.move_lines]
            sale_ids = sale_obj.search(cr, uid, [('procurement_group_id', '=',
                                                  picking.group_id.id)],
                                       context=context)
            if sale_ids:
                sale_line_ids = sale_line_obj.search(cr, uid,
                                                     [('order_id', 'in',
                                                       sale_ids),
                                                      ('product_id.type', '=',
                                                       'service')],
                                                     context=context)
                if sale_line_ids:
                    for line in sale_line_obj.browse(cr, uid, sale_line_ids,
                                                     context):
                        if line.pack_child_line_ids and not \
                                line.pack_parent_line_id and line.invoiced:
                            if sale_line_obj.pack_in_moves(cr, uid, line.id,
                                                           picking_product_ids,
                                                           context):
                                sale_line_obj.write(cr, uid, [line.id],
                                                    {'invoice_lines':
                                                     [(3, x.id) for x in
                                                      line.invoice_lines]},
                                                    context)
        new_picking_id, picking_type_id = \
            super(stock_return_picking, self)._create_returns(cr, uid, ids,
                                                              context)
        record_id = context and context.get('active_id', False) or False
        picking = self.pool.get('stock.picking').browse(cr, uid, record_id,
                                                        context)
        if picking.picking_type_id.code == 'outgoing':
            new_picking = self.pool.get('stock.picking').browse(
                cr, uid, new_picking_id, context)
            self.pool.get('stock.move').do_unreserve(
                cr, uid, [x.id for x in new_picking.move_lines], context)
            picking_type = self.pool.get('stock.picking.type').browse(
                cr, uid, picking_type_id, context)
            for move in new_picking.move_lines:
                move.location_dest_id = picking_type.default_location_dest_id.id
            self.pool.get('stock.move').action_assign(cr, uid,
                                                      [x.id for x in
                                                       new_picking.move_lines],
                                                      context)
            for move in new_picking.move_lines:
                for quant in move.reserved_quant_ids:
                    if quant.package_id:
                        self.pool.get('stock.quant').write(
                            cr, uid, quant.id, {'package_id': False}, context)
        return new_picking_id, picking_type_id
