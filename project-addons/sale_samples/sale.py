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

from openerp import fields, models, api, _
from openerp.tools import float_compare


class sale_order(models.Model):

    _inherit = 'sale.order'

    sample = fields.Boolean('Sample')

    def _prepare_order_line_procurement(self, cr, uid, order, line,
                                        group_id=False, context=None):
        res = super(sale_order, self)._prepare_order_line_procurement(cr, uid,
                                                                      order,
                                                                      line,
                                                                      group_id,
                                                                      context)
        if order.sample:
            res['invoice_state'] = 'none'
        return res

    def test_done_sample(self, cr, uid, ids, *args):
        res = False
        for sale in self.browse(cr, uid, ids):
            if sale.sample:
                for picking in sale.picking_ids:
                    if picking.state == 'done':
                        res = True
        return res

    @api.model
    def create(self, vals):
        res = super(sale_order, self).create(vals)
        if self.env.context.get('default_sample', False):
            res.sample = True
        return res


class sale_order_line(models.Model):

    _inherit = 'sale.order.line'

    sample_rel = fields.Boolean('Sample', related='order_id.sample')

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.order_id.sample:
            self.price_unit = 0.0
