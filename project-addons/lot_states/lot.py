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
from openerp import models, fields, api, exceptions, _


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    state = fields.Selection(
        (('draft', 'New'), ('in_rev', 'Revision(Q)'), ('revised', 'Revised'),
         ('approved', 'Approved'), ('rejected', 'Rejected')),
        'State', default='draft')

    state_depends = fields.Many2many('stock.production.lot',
                                     'final_material_lot_rel', 'final_lot_id',
                                     'material_lot_id', 'Dependencies')
    is_revised = fields.Boolean('Is material lots revised', compute='_is_revised')

    @api.one
    def _is_revised(self):
        self.is_revised = True
        for lot in self.state_depends:
            if lot.state == 'in_rev':
                self.is_revised = False
