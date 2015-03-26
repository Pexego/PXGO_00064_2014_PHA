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


class DuplicateProtocol(models.TransientModel):

    _name = 'quality.duplicate.protocol'

    def _get_protocol(self):
        return self.env.context.get('active_id')

    protocol_id = fields.Many2one('quality.protocol.report', 'Protocol',
                                  default=_get_protocol)
    product_ids = fields.Many2many('product.product',
                                   'product_duplicate_wizard_rel',
                                   'wiz_id', 'product_id', 'Products')

    @api.multi
    def duplicate(self):
        self.protocol_id.write({'product_ids':
                                [(3, x.id) for x in self.product_ids]})
        new_protocol = self.protocol_id.copy({'product_ids':
                                              [(4, x.id) for x in
                                               self.product_ids]})
        res = self.env.ref('quality_protocol_report.quality_protocol_report_form')
        return {
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': [res.id],
            'res_model': 'quality.protocol.report',
            'context': "{}",
            'type': 'ir.actions.act_window',
            'nodestroy': True,
            'target': 'current',
            'res_id': new_protocol.id
        }
