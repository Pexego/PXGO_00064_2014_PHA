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

from openerp import models, api
from openerp import workflow


class stock_picking(models.Model):
    _inherit = 'stock.picking'

    @api.cr_uid_ids_context
    def do_transfer(self, cr, uid, picking_ids, context=None):
        res = super(stock_picking, self).do_transfer(cr, uid, picking_ids,
                                                     context)
        for picking in self.browse(cr, uid, picking_ids, context):
            if picking.sale_id and picking.sale_id.sample:
                workflow.trg_write(uid, 'sale.order', picking.sale_id.id, cr)
        return res
