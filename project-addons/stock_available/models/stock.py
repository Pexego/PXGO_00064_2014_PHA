# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus I+D+i All Rights Reserved
#    $Iván Alvarez <informatica@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, orm, osv
from openerp import models, api
from openerp import tools, SUPERUSER_ID
from openerp.tools.translate import _
import openerp.addons.decimal_precision as dp
from openerp.addons.product import _common


class my_stock_available(osv.osv):

    _name = 'stock.available'

    _inherit = 'mrp.production'

    _columns = {
        'product_qty': fields.float('Product Quantity', digits_compute=dp.get_precision('Product Unit of Measure'),
                                    required=True, readonly=True, states={'draft': [('readonly', False)]}),
        'product_lines': fields.one2many('stock.available.product.line', 'production_id', 'Scheduled goods',
                                         readonly=True),
    }

    _defaults = {
        'state': lambda *a: 'draft',
        'product_qty': lambda *a: 1.0,
    }

    def action_compute(self, cr, uid, ids, properties=None, context=None):
        """ Computes bills of material of a product.
        @param properties: List containing dictionaries of properties.
        @return: No. of products.
        """
        return len(self._action_compute_lines(cr, uid, ids, properties=properties, context=context))

    def _action_compute_lines(self, cr, uid, ids, properties=None, context=None):
        """ Compute product_lines and workcenter_lines from BoM structure
        @return: product_lines
        """
        if properties is None:
            properties = []
        results = []
        bom_obj = self.pool.get('mrp.bom')
        uom_obj = self.pool.get('product.uom')
        #prod_line_obj = self.pool.get('mrp.production.product.line')
        prod_line_obj = self.pool.get('stock.available.product.line')
        #workcenter_line_obj = self.pool.get('mrp.production.workcenter.line')
        for production in self.browse(cr, uid, ids, context=context):
            #unlink product_lines
            prod_line_obj.unlink(cr, SUPERUSER_ID, [line.id for line in production.product_lines], context=context)
            #unlink workcenter_lines
            #workcenter_line_obj.unlink(cr, SUPERUSER_ID, [line.id for line in production.workcenter_lines], context=context)
            # search BoM structure and route
            bom_point = production.bom_id
            bom_id = production.bom_id.id
            if not bom_point:
                bom_id = bom_obj._bom_find(cr, uid, production.product_uom.id, product_id=production.product_id.id, properties=properties, context=context)
                if bom_id:
                    bom_point = bom_obj.browse(cr, uid, bom_id)
                    routing_id = bom_point.routing_id.id or False
                    self.write(cr, uid, [production.id], {'bom_id': bom_id, 'routing_id': routing_id})

            if not bom_id:
                raise osv.except_osv(_('Error!'), _("Cannot find a bill of material for this product."))

            # get components and workcenter_lines from BoM structure
            factor = uom_obj._compute_qty(cr, uid, production.product_uom.id, production.product_qty, bom_point.product_uom.id)
            # product_lines, workcenter_lines
            results, results2 = bom_obj._bom_explode(cr, uid, bom_point, production.product_id, factor / bom_point.product_qty, properties, routing_id=production.routing_id.id, context=context)
            # reset product_lines in production order
            for line in results:
                line['production_id'] = production.id
                prod_line_obj.create(cr, uid, line)

            #reset workcenter_lines in production order
            for line in results2:
                line['production_id'] = production.id
                #workcenter_line_obj.create(cr, uid, line)
        return results

my_stock_available()


class my_stock_available_production_product_line(osv.osv):

    _name = 'stock.available.product.line'
    _inherit = 'mrp.production.product.line'
    _description = 'Production Scheduled Product'
    _columns = {
        'name': fields.char('Name', required=True),
        'product_id': fields.many2one('product.product', 'Product', required=True),
        'product_qty': fields.float('Product Quantity', digits_compute=dp.get_precision('Product Unit of Measure'), required=True),
        'product_uom': fields.many2one('product.uom', 'Product Unit of Measure', required=True),
        'product_uos_qty': fields.float('Product UOS Quantity'),
        'product_uos': fields.many2one('product.uom', 'Product UOS'),
        'production_id': fields.many2one('stock.available', 'Production Order', select=True),
        'product_qty_available': fields.related('product_id', 'qty_available', type='float', string='Quantity On Hand',
                                                readonly=True),
    }

my_stock_available_production_product_line()