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
from openerp import models, fields, api, exceptions, _

class ChangeProductionQty(models.TransientModel):

    _inherit = 'change.production.qty'

    @api.multi
    def change_prod_qty(self):
        res = super(ChangeProductionQty, self).change_prod_qty()
        production_id = self.env.context.get('active_id', False)
        production = self.env['mrp.production'].browse(production_id)
        for line in production.move_lines:
            if len(line.move_orig_ids) != 1:
                raise exceptions.Warning(
                    _('Not implemented error'),
                    _('Qty change not implemented for moves with several \
origins'))
            for orig_move in line.move_orig_ids:
                orig_move.do_unreserve()
                orig_move.product_uom_qty = line.product_uom_qty
        return res
