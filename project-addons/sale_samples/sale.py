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

from openerp import fields, models, api
from openerp.tools.translate import _
from openerp.tools import float_compare

class sale_order(models.Model):

    _inherit = 'sale.order'

    sample = fields.Boolean('Sample')

    def _prepare_order_line_procurement(self, cr, uid, order, line, group_id=False, context=None):
        res = super(sale_order,self)._prepare_order_line_procurement(cr, uid, order, line, group_id, context)
        if order.sample:
            res['invoice_state'] = 'none'
        return res

class sale_order_line(models.Model):

    _inherit = 'sale.order.line'

    sample_rel = fields.Boolean('Sample', compute='_get_sample')

    @api.one
    @api.depends('order_id.sample')
    def _get_sample(self):
        self.sample_rel = self.order_id.sample

    def create(self, cr, uid, vals, context={}):
        order_id = vals.get('order_id', False)
        if order_id:
            sample = self.pool.get('sale.order').read(cr, uid, order_id,
                                                      ['sample'],
                                                      context)['sample']
            context['sample'] = sample
        return super(sale_order_line, self).create(cr, uid, vals, context)

    def product_id_change(self, cr, uid, ids, pricelist, product, qty=0,
                          uom=False, qty_uos=0, uos=False, name='',
                          partner_id=False, lang=False, update_tax=True,
                          date_order=False, packaging=False,
                          fiscal_position=False, flag=False, context=None):

        res = super(sale_order_line, self).product_id_change(cr, uid, ids,
                                                             pricelist,
                                                             product, qty, uom,
                                                             qty_uos, uos,
                                                             name, partner_id,
                                                             lang, update_tax,
                                                             date_order,
                                                             packaging,
                                                             fiscal_position,
                                                             flag, context)
        if not res.get('value', False):
            return res
        if res['value'].get('price_unit', False) and \
                context.get('sample', False):
            res['value']['price_unit'] = 0.0
        if res['value'].get('tax_id', False) and \
                context.get('sample', False):
            res['value']['tax_id'] = None
        return res

    def product_id_change_with_wh(self, cr, uid, ids, pricelist, product,
                                  qty=0, uom=False, qty_uos=0, uos=False,
                                  name='', partner_id=False, lang=False,
                                  update_tax=True, date_order=False,
                                  packaging=False, fiscal_position=False,
                                  flag=False, warehouse_id=False,
                                  context=None):
        """
            Se sobreescribe el metodo del moulo sale_stock para que no
            se salte el product_id_change de esta clase al llamar a super
        """
        context = context or {}
        product_uom_obj = self.pool.get('product.uom')
        product_obj = self.pool.get('product.product')
        warning = {}
        res = self.product_id_change(cr, uid, ids, pricelist, product, qty=qty,
            uom=uom, qty_uos=qty_uos, uos=uos, name=name, partner_id=partner_id,
            lang=lang, update_tax=update_tax, date_order=date_order,
            packaging=packaging, fiscal_position=fiscal_position, flag=flag, context=context)

        if not product:
            res['value'].update({'product_packaging': False})
            return res

        #update of result obtained in super function
        product_obj = product_obj.browse(cr, uid, product, context=context)
        res['value']['delay'] = (product_obj.sale_delay or 0.0)

        # Calling product_packaging_change function after updating UoM
        res_packing = self.product_packaging_change(cr, uid, ids, pricelist, product, qty, uom, partner_id, packaging, context=context)
        res['value'].update(res_packing.get('value', {}))
        warning_msgs = res_packing.get('warning') and res_packing['warning']['message'] or ''

        #determine if the product is MTO or not (for a further check)
        isMto = False
        if warehouse_id:
            warehouse = self.pool.get('stock.warehouse').browse(cr, uid, warehouse_id, context=context)
            for product_route in product_obj.route_ids:
                if warehouse.mto_pull_id and warehouse.mto_pull_id.route_id and \
                        warehouse.mto_pull_id.route_id.id == product_route.id:
                    isMto = True
                    break
        else:
            try:
                mto_route_id = self.pool.get('ir.model.data').get_object(cr, uid, 'stock', 'route_warehouse0_mto').id
            except:
                # if route MTO not found in ir_model_data, we treat the product as in MTS
                mto_route_id = False
            if mto_route_id:
                for product_route in product_obj.route_ids:
                    if product_route.id == mto_route_id:
                        isMto = True
                        break

        # check if product is available, and if not: raise a warning, but do
        # this only for products that aren't processed in MTO
        if not isMto:
            uom2 = False
            if uom:
                uom2 = product_uom_obj.browse(cr, uid, uom, context=context)
                if product_obj.uom_id.category_id.id != uom2.category_id.id:
                    uom = False
            if not uom2:
                uom2 = product_obj.uom_id
            compare_qty = float_compare(product_obj.virtual_available, qty, precision_rounding=uom2.rounding)
            if (product_obj.type=='product') and int(compare_qty) == -1:
                warn_msg = _('You plan to sell %.2f %s but you only have %.2f %s available !\nThe real stock is %.2f %s. (without reservations)') % \
                    (qty, uom2.name,
                     max(0,product_obj.virtual_available), uom2.name,
                     max(0,product_obj.qty_available), uom2.name)
                warning_msgs += _("Not enough stock ! : ") + warn_msg + "\n\n"

        #update of warning messages
        if warning_msgs:
            warning = {
                       'title': _('Configuration Error!'),
                       'message' : warning_msgs
                    }
        res.update({'warning': warning})
        return res
