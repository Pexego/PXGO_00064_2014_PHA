# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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

from openerp import models, fields, _, exceptions


class MrpProduction(models.Model):

    _inherit = "mrp.production"

    adjustsments_ids = fields.One2many('mrp.production.adjustments',
                                       'production_id', 'Adjustments')
    goods_request_date = fields.Date('Request date')
    goods_return_date = fields.Date('Return date')
    picking_notes = fields.Text('Picking notes')

    def action_assign(self, cr, uid, ids, context=None):
        """
        Checks the availability on the consume lines of the production order
        """
        for production in self.browse(cr, uid, ids, context=context):
            for move in production.move_lines:
                if move.raw_material_production_id and move.served_qty:
                    if move.served_qty != move.product_uom_qty:
                        raise exceptions.Warning(_("""Cannot produce because
 move quantity %s and served quantity %s don't match""") %
                                                 (str(move.product_uom_qty),
                                                  str(move.served_qty)))
        return super(MrpProduction, self).action_assign(cr, uid, ids,
                                                        context=context)
