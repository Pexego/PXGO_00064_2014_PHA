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
from openerp import models


class StockMove(models.Model):

    _inherit = 'stock.move'

    def _create_invoice_line_from_vals(self, cr, uid, move, invoice_line_vals, context=None):
        res = super(StockMove, self)._create_invoice_line_from_vals(cr, uid, move, invoice_line_vals, context)
        if move.purchase_line_id:
            self.pool.get('account.invoice.line').write(cr, uid, res, {'analytics_id': move.purchase_line_id.analytics_id.id})
        return res
