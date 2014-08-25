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

from openerp import models, fields, exceptions
from openerp.tools.translate import _


class stock_picking(models.Model):

    _inherit = 'stock.picking'

    def _create_invoice_from_picking(self, cr, uid, picking, vals,
                                     context=None):
        sale_obj = self.pool.get('sale.order')
        sale_line_obj = self.pool.get('sale.order.line')
        invoice_line_obj = self.pool.get('account.invoice.line')
        invoice_id = super(stock_picking,
                           self)._create_invoice_from_picking(cr, uid, picking,
                                                              vals,
                                                              context=context)
        if picking.group_id:
            sale_ids = sale_obj.search(cr, uid,
                                       [('procurement_group_id', '=',
                                         picking.group_id.id)],
                                       context=context)
            if sale_ids:
                sale_line_ids = sale_line_obj.search(cr, uid,
                                                     [('order_id', 'in',
                                                       sale_ids),
                                                      ('replacement', '=',
                                                       True),
                                                      ('invoiced', '=',
                                                       False)],
                                                     context=context)
                if sale_line_ids:
                    created_lines = sale_line_obj.invoice_line_create(
                        cr, uid, sale_line_ids, context=context)
                    invoice_line_obj.write(cr, uid, created_lines,
                                           {'invoice_id': invoice_id},
                                           context=context)
        return invoice_id