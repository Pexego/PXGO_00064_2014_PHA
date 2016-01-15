# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
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
from openerp import models, fields, api, exceptions, _


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    @api.model
    def _search(self, args, offset=0, limit=0, order=None, count=False,
                access_rights_uid=None):
        if self._context.get('product_id', False) and \
                self._context.get('location_id', False):
            quants = self.env['stock.quant'].search(
                [('location_id', '=', self._context.get('location_id')),
                 ('product_id', '=', self._context.get('product_id')),
                 ('lot_id', '!=', False)])
            lot_ids = [x.lot_id.id for x in quants]
            args = [('id', 'in', lot_ids)] + args
        return super(StockProductionLot, self)._search(
            args, offset, limit, order, count=count,
            access_rights_uid=access_rights_uid)
