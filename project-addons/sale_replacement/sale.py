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
from datetime import date


class sale_order(models.Model):

    _inherit = "sale.order"

    replacement = fields.Boolean('Replacement')
    rep_lines = fields.One2many('sale.order.line', 'orig_sale', 'Rep lines')
    is_all_invoiced = fields.Boolean('Is invoiced', compute='_get_replacement_invoiced')

    @api.one
    def _get_replacement_invoiced(self):
        is_all_invoiced = True
        for line in self.order_line:
            if not line.is_all_replaced:
                is_all_invoiced = False
        self.is_all_invoiced = is_all_invoiced

    @api.model
    def execute_onchanges(self, partner_id, line):
        par_val = self.onchange_partner_id(partner_id)['value']
        line.update(self.env['sale.order.line'].product_id_change_with_wh(
            par_val['pricelist_id'], line['product_id'], line['product_uom_qty'],
            partner_id=partner_id, date_order=date.today().strftime('%Y-%m-%d'),
            fiscal_position=par_val.get('fiscal_position', False),
            warehouse_id=self._get_default_warehouse())['value'])
        return line

    @api.model
    def default_get(self, fields):
        res = super(sale_order, self).default_get(fields)
        if self._context.get('order_line', False) and res.get('partner_id'):
            # Se debe ejecutar el onchange del producto manualmente
            final_line_vals = []
            for line_vals in eval(self._context.get('order_line')):
                final_line_vals.append((0, 0, self.execute_onchanges(res['partner_id'], line_vals[2])))
            res['order_line'] = final_line_vals
        return res

    @api.multi
    def view_invoiced_qtys(self):
        action_data = self.env.ref('sale_replacement.action_replacements_to_invoice').read()[0]

        action_data['context'] = {}
        action_data['domain'] = [('order_id', 'in', self.ids)]
        return action_data

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        res = super(sale_order, self)._prepare_order_line_procurement(order,
                                                                      line,
                                                                      group_id)
        if order.replacement:
            res['invoice_state'] = 'none'
        return res

    @api.multi
    def test_done_replacement(self, *args):
        res = False
        for sale in self:
            if sale.replacement:
                for picking in sale.picking_ids:
                    if picking.state == 'done':
                        res = True
        return res

    @api.model
    def test_no_product(self, order):
        for line in order.order_line:
            if (line.product_id and (line.product_id.type != 'service')) \
                    and not line.replacement:
                return False
        return True

    @api.multi
    def has_stockable_products(self, *args):
        for order in self:
            for order_line in order.order_line:
                if (order_line.product_id and
                        order_line.product_id.type in ('product', 'consu')) \
                        and not order_line.replacement:
                    return True
        return False

    @api.multi
    def action_button_confirm(self):
        for order in self:
            for line in order.order_line:
                if line.replacement:
                    line._get_orig_line()
        return super(sale_order, self).action_button_confirm()


class sale_order_line(models.Model):

    _inherit = "sale.order.line"

    replacement = fields.Boolean('Replacement')

    qty_replaced = fields.Float('Quantity replacement',
                                compute='_get_qty_replaced', store=True)
    replaced_returned_qty = fields.Float('')

    is_all_replaced = fields.Boolean('All replaced',
                                     compute="_get_is_all_replaced",
                                     store=True)

    is_sale_replacement = fields.Boolean('is sale replacement',
                                         related='order_id.replacement',
                                         readonly=True)

    orig_sale = fields.Many2one('sale.order', 'Original order')


    from openerp.osv import fields as fields2

    def _fnct_line_invoiced(self, cr, uid, ids, field_name, args,
                            context=None):
        res = dict.fromkeys(ids, False)
        for this in self.browse(cr, uid, ids, context=context):
            res[this.id] = this.invoice_lines and \
                all(iline.invoice_id.state != 'cancel'
                    for iline in this.invoice_lines)
            if this.order_id.replacement:
                sale_lines = self.search(
                    cr, uid, [('replacement', '=', True),
                              ('orig_sale', '=', this.order_id.id)],
                    context=context)
                for sale_line in sale_lines:
                    res[sale_line] = res[this.id]
        return res

    def _order_lines_from_invoice(self, cr, uid, ids, context=None):
        cr.execute("""SELECT DISTINCT sol.id FROM sale_order_invoice_rel rel
                      JOIN sale_order_line sol ON (sol.order_id = rel.order_id)
                      WHERE rel.invoice_id = ANY(%s)""", (list(ids),))
        line_ids = [i[0] for i in cr.fetchall()]
        for line in self.pool.get('sale.order.line').browse(cr, uid, line_ids,
                                                            context):
            if line.product_id:
                cr.execute("""SELECT sol.id from sale_order_line sol where
                              sol.product_id = %s and sol.orig_sale = %s""",
                           (line.product_id.id, line.order_id.id))
                line_ids += [i[0] for i in cr.fetchall()]
        return line_ids

    _columns = {
        'invoiced': fields2.function(_fnct_line_invoiced, string='Invoiced',
                                     type='boolean',
                                     store={
                                         'account.invoice':
                                         (_order_lines_from_invoice, ['state'],
                                          10),
                                         'sale.order.line':
                                         (lambda self, cr, uid, ids, ctx=None:
                                             ids,
                                          ['invoice_lines'], 10)
                                     })
    }

    @api.one
    @api.depends('order_id.rep_lines.state', 'replaced_returned_qty')
    def _get_qty_replaced(self):
        rep_lines = self.search_read(
            [('product_id', '=', self.product_id.id),
             ('orig_sale', '=', self.order_id.id),
             ('state', 'not in', ('draft', 'sent', 'cancel'))],
            ['product_uom_qty'])
        self.qty_replaced = sum([x['product_uom_qty'] for x in rep_lines]) + self.replaced_returned_qty

    @api.one
    @api.depends('product_uom_qty', 'qty_replaced')
    def _get_is_all_replaced(self):
        self.is_all_replaced = self.product_uom_qty - self.qty_replaced == 0 \
            and True or False

    @api.multi
    def need_procurement(self):
        # when sale is installed alone, there is no need to create
        # procurements, but with sale_stock we must create a procurement
        # for each product that is not a service.
        for line in self:
            if not line.replacement:
                return super(sale_order_line, self).need_procurement()
        return False

    @api.multi
    def _get_orig_line(self):
        """
        :return: the browse record of original line for the replacement.
        """
        self.ensure_one()
        sale_id = self.orig_sale.id
        orig_line = self.search([('order_id', '=', sale_id),
                                 ('product_id', '=',
                                  self.product_id.id)])
        if not orig_line:
            raise exceptions.MissingError(
                _('Not found the original line of replacement'))
        if (orig_line.product_uom_qty - orig_line.qty_replaced) < \
                self.product_uom_qty and not \
                self._context.get('no_control_qty', False):
            raise exceptions.MissingError(
                _('Qty error in replacement.'))

        return orig_line

    @api.multi
    def invoice_line_create(self):
        create_ids = []
        sales = set()
        for line in self:
            vals = self._prepare_order_line_invoice_line(line, False)
            ids = self.env['sale.order.line']
            if vals:
                if line.replacement:
                    orig = line.with_context(no_control_qty=True)._get_orig_line()
                    ids += orig
                else:
                    ids += line
                inv = self.env['account.invoice.line'].create(vals)
                ids.write({'invoice_lines': [(4, inv.id)]})
                sales.add(line.order_id.id)
                create_ids.append(inv.id)
        # Trigger workflow events
        for sale_id in sales:
            workflow.trg_write(self.env.user.id, 'sale.order', sale_id, self.env.cr)
        return create_ids

    @api.multi
    def _get_appropiate_account(self):
        self.ensure_one()
        if self.product_id:
            account_id = self.product_id.property_account_income.id
            if not account_id:
                account_id = self.product_id.categ_id.property_account_income_categ.id
            if not account_id:
                raise exceptions.Warning(
                    _('Error!'),
                    _('Please define income account for this product: \
                       "%s" (id:%d).') %
                    (self.product_id.name, self.product_id.id,))
        else:
            prop = self.pool.get('ir.property').get(
                cr, uid, 'property_account_income_categ',
                'product.category', context=context)
            account_id = prop and prop.id or False
        return account_id

    @api.model
    def _prepare_order_line_invoice_line(self, line, account_id=False):
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
                account_id = line._get_appropiate_account()
            uosqty = self._get_line_qty(line)
            uos_id = self._get_line_uom(line)
            pu = 0.0
            if uosqty:
                orig_line = line.with_context(no_control_qty=True)._get_orig_line()
                precision = self.env['decimal.precision'].precision_get('Product Price')
                pu = round(
                    orig_line.price_unit * line.product_uom_qty / uosqty,
                    precision)
            fpos = line.order_id.fiscal_position or self.env['account.fiscal.position']
            account_id = fpos.map_account(account_id)
            if not account_id:
                raise exceptions.Warning(
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
                         self)._prepare_order_line_invoice_line(line,
                                                                account_id)

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
            warning = warning is not False and warning or \
                {'title': 'Replacement error', 'message': ''}
            if not origin_sale:
                warning['message'] += _('Not found the original sale.\n')
            orig_line_id = self.search(cr, uid,
                                       [('order_id', '=', origin_sale),
                                        ('product_id', '=', product),
                                        ('is_all_replaced', '=', False)],
                                       context=context)
            if not orig_line_id:
                warning['message'] += _('Not found the original sale line.\n')
            line = self.browse(cr, uid, orig_line_id[0], context)
            if (line.product_uom_qty - line.qty_replaced) < qty:
                res['value']['product_uom_qty'] = line.product_uom_qty - line.qty_replaced
                res['value']['product_uos_qty'] = line.product_uom_qty - line.qty_replaced
                warning['message'] += _('The quantity is bigger than the original.\n')
            res['value']['price_unit'] = line.price_unit
            if len(warning['message']):
                res['warning'] = warning

        return res
