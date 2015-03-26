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


class MrpReleaseAll(models.TransientModel):

    _name = 'mrp.release.all.wizard'

    final_qty = fields.Float('Final quantity')

    @api.model
    def default_get(self, fields):
        data = super(MrpReleaseAll, self).default_get(fields)
        mrp_id = self.env.context.get('active_id', False)
        mrp = self.env['mrp.production'].browse(mrp_id)
        data['final_qty'] = sum([x.product_uom_qty for x in
                                 mrp.move_created_ids])
        return data

    @api.multi
    def release(self):
        mrp_id = self.env.context.get('active_id', False)
        mrp = self.env['mrp.production'].browse(mrp_id)
        produce_wiz = self.env['mrp.product.produce'].create({'mode': 'consume_produce'})
        produce_wiz.product_qty = self.final_qty
        produce_wiz.consume_lines = False
        produce_wiz.do_produce()
        mrp.signal_workflow('button_produce_done')
        mrp.final_lot_id.signal_workflow('direct_approved')
        return {'type': 'ir.actions.act_window_close'}
