# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, tools, exceptions, _


class sale_order_to_invoice_replacement(models.Model):

    _name = 'sale.order.to.invoice.replacement'
    _auto = False

    order_id = fields.Many2one('sale.order', 'Order')
    partner_id = fields.Many2one('res.partner', 'Partner')
    product_id = fields.Many2one('product.product', 'Product')
    quantity = fields.Float('Sale quantity')
    quantity_invoiced = fields.Float('Quantity invoiced')

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE VIEW sale_order_to_invoice_replacement as (
SELECT sol.id as id, sol.order_id as order_id, so.partner_id as partner_id, sol.product_id as product_id,
       sol.product_uom_qty as quantity,  sol.qty_replaced as quantity_invoiced
FROM sale_order_line sol
JOIN sale_order so on sol.order_id = so.id
WHERE so.replacement = TRUE and sol.product_uom_qty - sol.qty_replaced != 0
GROUP BY sol.id, sol.order_id, so.partner_id, sol.product_id, sol.product_uom_qty, quantity_invoiced)
""")
