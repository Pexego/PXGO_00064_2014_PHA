# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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
from openerp import models, fields, api
from datetime import date


class mrp_partial_release_log(models.Model):

    _name = 'mrp.partial.release.log'

    production_id = fields.Many2one('mrp.production', 'Production',
                                    required=True)
    product_id = fields.Many2one('product.product', 'Product', required=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True)
    date = fields.Date('Date', required=True)
    quantity = fields.Float('Quantity', required=True)
    user_id = fields.Many2one('res.users', 'User', required=True)
    reason = fields.Char('Reason')

    @api.multi
    def create_release_log(self, production, release_wiz):
        log_vals = {
            'production_id': production.id,
            'product_id': production.product_id.id,
            'lot_id': production.final_lot_id.id,
            'date': date.today(),
            'quantity': release_wiz.release_qty,
            'user_id': self.env.uid,
            'reason': release_wiz.reason,
        }
        return self.create(log_vals)
