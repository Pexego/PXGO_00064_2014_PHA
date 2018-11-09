# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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


class MrpPartialRelease(models.TransientModel):

    _name = "mrp.partial.release"
    release_qty = fields.Float('Release Quantity')
    reason = fields.Char('Reason', required=True)

    @api.multi
    def release(self):
        produce_wiz = self.env['mrp.product.produce'].create(
            {'mode': 'only_produce'})
        produce_wiz.product_qty = self.release_qty
        produce_wiz.consume_lines = False
        produce_wiz.with_context(
            ignore_child=True, not_cancel=True).do_produce()
        production = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False))
        self.env['mrp.partial.release.log'].create_release_log(production,
                                                               self)
        # Si la liberación parcial es mayor o igual a la cantidad total
        # de la producción debemos duplicar un movimiento, ya que si
        # no quedan movimientos en productos a fabricar no nos permitirá
        # liberar más
        if not production.move_created_ids:
            production.move_created_ids2[0].copy({'production_id': production.id, 'product_uom_qty': 1})
        return True
