# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
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
from openerp import models, api, fields


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    partial_ids = fields.One2many(comodel_name='stock.picking',
                                  inverse_name='backorder_id')
    has_partials_transferred_or_invoiced = fields.Boolean(
                                compute='_has_partials_transferred_or_invoiced')
    can_be_fully_reverted = fields.Boolean(compute='_can_be_fully_reverted')

    @api.one
    @api.depends('partial_ids')
    def _has_partials_transferred_or_invoiced(self):
        res = False
        for partial in self.partial_ids:
            res = res or \
                  (partial.invoice_state == 'invoiced') or \
                  (partial.state == 'done')
        self.has_partials_transferred_or_invoiced = res

    @api.one
    @api.depends('state',
                 'picking_type_code',
                 'invoice_state',
                 'backorder_id')
    def _can_be_fully_reverted(self):
        self.can_be_fully_reverted = (self.state == 'done') and \
                                     (self.picking_type_code == 'outgoing') and \
                                     (self.invoice_state != 'invoiced') and \
                                     (len(self.sale_id) > 0)
#                                     (len(self.backorder_id) == 0) and \
