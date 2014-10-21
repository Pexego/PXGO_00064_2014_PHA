# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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

from openerp import models, fields, exceptions, api, workflow
from openerp.tools.translate import _

class sale_order(models.Model):

    _inherit = "sale.order"

    replacement = fields.Boolean('Replacement')

    def _prepare_order_line_procurement(self, cr, uid, order, line,
                                        group_id=False, context=None):
        res = super(sale_order, self)._prepare_order_line_procurement(cr, uid,
                                                                      order,
                                                                      line,
                                                                      group_id,
                                                                      context)
        if order.replacement:
            res['invoice_state'] = 'none'
        return res

    def test_done_replacement(self, cr, uid, ids, *args):
        res = False
        for sale in self.browse(cr, uid, ids):
            if sale.replacement:
                for picking in sale.picking_ids:
                    if picking.state == 'done':
                        res = True
        return res

    def test_no_product(self, cr, uid, order, context):
        for line in order.order_line:
            if (line.product_id and (line.product_id.type != 'service')) \
                    and not line.replacement:
                return False
        return True

    def has_stockable_products(self, cr, uid, ids, *args):
        for order in self.browse(cr, uid, ids):
            for order_line in order.order_line:
                if (order_line.product_id and
                        order_line.product_id.type in ('product', 'consu')) \
                        and not order_line.replacement:
                    return True
        return False

    def action_button_confirm(self, cr, uid, ids, context=None):
        line_obj = self.pool.get('sale.order.line')
        for order in self.browse(cr, uid, ids, context):
            for line in order.order_line:
                if line.replacement:
                    line_obj._get_orig_line(cr, uid, line, context)
        return super(sale_order, self).action_button_confirm(cr, uid,
                                                             ids,
                                                             context)


class sale_order_line(models.Model):

    _inherit = "sale.order.line"

    replacement = fields.Boolean('Replacement')

    qty_replacement = fields.Float('Quantity replacement')

    is_all_replacement = fields.Float('All replacement',
                                      compute="_is_all_replacement")

    is_sale_replacement = fields.Boolean('is sale replacement', related='order_id.replacement')

    orig_sale = fields.Many2one('sale.order', 'Original order')

    @api.depends('product_uom_qty', 'qty_replacement')
    def _is_all_replacement(self):
        self.is_all_replacement = self.product_uom_qty - \
            self.qty_replacement == 0 or False

    def need_procurement(self, cr, uid, ids, context=None):
        # when sale is installed alone, there is no need to create
        # procurements, but with sale_stock we must create a procurement
        # for each product that is not a service.
        for line in self.browse(cr, uid, ids, context=context):
            if not line.replacement:
                return super(sale_order_line, self).need_procurement(
                    cr, uid, ids, context=context)
        return False

    def _get_orig_line(self, cr, uid, line, context={}):
        """
        :param cr: db cursor
        :param uid: user_id
        :param line: browse_record of sale.order.line
        :param context: context
        :return: the browse record of original line for the replacement.
        """
        sale_id = line.orig_sale.id
        orig_line_id = self.search(cr, uid,
                                   [('order_id', '=', sale_id),
                                    ('product_id', '=',
                                     line.product_id.id),
                                    ('is_all_replacement', '=', False)],
                                   context=context)
        if not orig_line_id:
            raise exceptions.MissingError(
                _('Not found the original line of replacement'))
        orig_line = self.browse(cr, uid, orig_line_id[0], context)
        if (orig_line.product_uom_qty - orig_line.qty_replacement) < \
                line.product_uom_qty and not context.get('no_control_qty'):
            raise exceptions.MissingError(
                _('Qty error in replacement.'))

        return orig_line

    def invoice_line_create(self, cr, uid, ids, context=None):
        if context is None:
            context = {}

        create_ids = []
        sales = set()
        for line in self.browse(cr, uid, ids, context=context):
            vals = self._prepare_order_line_invoice_line(cr, uid, line, False,
                                                         context)
            ids = []
            if vals:
                if line.replacement:
                    context['no_control_qty'] = True
                    orig = self._get_orig_line(cr, uid, line, context)
                    context.pop('', False)
                    ids.append(orig.id)
                else:
                    ids.append(line.id)
                inv_id = self.pool.get('account.invoice.line').create(cr, uid, vals, context=context)
                self.write(cr, uid, ids, {'invoice_lines': [(4, inv_id)]}, context=context)
                sales.add(line.order_id.id)
                create_ids.append(inv_id)
        # Trigger workflow events
        for sale_id in sales:
            workflow.trg_write(uid, 'sale.order', sale_id, cr)
        return create_ids

    def _prepare_order_line_invoice_line(self, cr, uid, line, account_id=False,
                                         context=None):
        """Prepare the dict of values to create the new invoice line for a
           sales order line. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record line: sale.order.line record to invoice
           :param int account_id: optional ID of a G/L account to force
               (this is used for returning products including service)
           :return: dict of values to create() the invoice line

           MOD: Si la linea está marcada como reemplazo, se factura con el
           precio original.
        """
        res = {}
        if line.replacement and not line.invoiced:
            if not account_id:
                if line.product_id:
                    account_id = line.product_id.property_account_income.id
                    if not account_id:
                        account_id = line.product_id.categ_id.property_account_income_categ.id
                    if not account_id:
                        raise exceptions.except_orm(
                            _('Error!'),
                            _('Please define income account for this product: \
                               "%s" (id:%d).') %
                            (line.product_id.name, line.product_id.id,))
                else:
                    prop = self.pool.get('ir.property').get(
                        cr, uid, 'property_account_income_categ',
                        'product.category', context=context)
                    account_id = prop and prop.id or False
            uosqty = self._get_line_qty(cr, uid, line, context=context)
            uos_id = self._get_line_uom(cr, uid, line, context=context)
            pu = 0.0
            if uosqty:
                orig_line = self._get_orig_line(cr, uid, line, context)
                qty_replacement = orig_line.qty_replacement + \
                    line.product_uom_qty
                self.write(cr, uid, [orig_line.id],
                           {'qty_replacement': qty_replacement}, context)
                precision = self.pool.get('decimal.precision').precision_get(
                    cr, uid, 'Product Price')
                pu = round(
                    orig_line.price_unit * line.product_uom_qty / uosqty,
                    precision)
            fpos = line.order_id.fiscal_position or False
            fisc_pos_obj = self.pool.get('account.fiscal.position')
            account_id = fisc_pos_obj.map_account(cr, uid, fpos, account_id)
            if not account_id:
                raise exceptions.except_orm(
                    _('Error!'),
                    _('There is no Fiscal Position defined or Income  \
                       category account defined for default properties of \
                       Product categories.'))
            res = {
                'name': line.name,
                'sequence': line.sequence,
                'origin': line.order_id.name,
                'account_id': account_id,
                'price_unit': pu,
                'quantity': uosqty,
                'discount': line.discount,
                'uos_id': uos_id,
                'product_id': line.product_id.id or False,
                'invoice_line_tax_id': [(6, 0, [x.id for x in line.tax_id])],
                'account_analytic_id':
                line.order_id.project_id and
                line.order_id.project_id.id or False,
            }
            return res
        else:
            return super(sale_order_line,
                         self)._prepare_order_line_invoice_line(cr, uid, line,
                                                                account_id,
                                                                context)

    def product_id_change(
            self, cr, uid, ids, pricelist, product, qty=0, uom=False,
            qty_uos=0, uos=False, name='', partner_id=False, lang=False,
            update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False, context=None):
        """
            Modify the onchange of product_id, if the replacement checkbox
            is True use the price_unit of the origin_sale.
        """

        if not context:
            context = {}
        replacement = context.get('rep', False)
        origin_sale = context.get('orig', False)
        res = super(sale_order_line, self).product_id_change(
            cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, context)
        if replacement:
            warning = res.get('warning', False)
            warning = warning != False and warning or {'title': 'Replacement error', 'message': ''}
            if not origin_sale:
                warning['message'] += _('Not found the original sale.\n')
            orig_line_id = self.search(cr, uid,
                               [('order_id', '=', origin_sale),
                                ('product_id', '=', product),
                                ('is_all_replacement', '=', False)],
                               context=context)
            if not orig_line_id:
                warning['message'] += _('Not found the original sale line.\n')
            line = self.browse(cr, uid, orig_line_id[0], context)
            if (line.product_uom_qty - line.qty_replacement) < qty:
                res['value']['product_uom_qty'] = line.product_uom_qty - line.qty_replacement
                res['value']['product_uos_qty'] = line.product_uom_qty - line.qty_replacement
                warning['message'] += _('The quantity is bigger than the original.\n')
            res['value']['price_unit'] = line.price_unit
            if len(warning['message']):
                res['warning'] = warning

        return res
