# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
#    $Oscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, api


class StockMove(models.Model):
    _inherit = 'stock.move'

    @api.model
    def _get_invoice_line_vals(self, move, partner, inv_type):
        res = super(StockMove, self)._get_invoice_line_vals(move, partner,
                                                            inv_type)
        if inv_type in ('out_invoice', 'out_refund') and move.procurement_id and\
                move.procurement_id.sale_line_id:
            sale_line = move.procurement_id.sale_line_id
            res['commercial_discount'] = sale_line.commercial_discount
            res['financial_discount'] = sale_line.financial_discount
            res['move_id'] = move.id

        if move.purchase_line_id:
            purchase_line = move.purchase_line_id
            res['commercial_discount'] = purchase_line.commercial_discount
            res['financial_discount'] = purchase_line.financial_discount
            res['move_id'] = move.id
        return res