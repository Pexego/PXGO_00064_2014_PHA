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


class sale_order(models.Model):

    _inherit = 'sale.order'

    sample = fields.Boolean('Sample')

class sale_order_line(models.Model):

    _inherit = 'sale.order.line'

    sample_rel = fields.Boolean('Sample', compute='_get_sample')

    @api.one
    @api.depends('order_id.sample')
    def _get_sample(self):
        self.sample_rel = self.order_id.sample

    @api.v7
    def product_id_change_with_sample(self, cr, uid, ids, pricelist, product, qty=0,
            uom=False, qty_uos=0, uos=False, name='', partner_id=False,
            lang=False, update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False, warehouse_id=False, context=None, sample=None):
        res = super(sale_order_line,self).product_id_change_with_wh(cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name, partner_id,
            lang, update_tax, date_order, packaging, fiscal_position, flag, warehouse_id, context)
        if res.get('value', {}).get('price_unit', False) and sample:
            res['value']['price_unit'] = 0.0
        return res
