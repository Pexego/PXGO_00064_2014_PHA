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
from openerp import models, fields, api


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    response_ids = fields.One2many('survey.user_input', 'lot_id', 'Responses')


class StockMove(models.Model):

    _inherit = "stock.move"

    acceptance_date = fields.Date('Acceptance date')
    orig_acceptance_date = fields.Date(
        'Acceptance date', related='move_orig_ids.acceptance_date')
    initials = fields.Char('Initials')
    initials_acond = fields.Char('Initials')
    workcenter_id = fields.Many2one('mrp.workcenter', 'Workcenter')
    used_lot = fields.Char('Used lot')
    checked_disp = fields.Boolean('Checked availability')
    qty_used = fields.Float('Qty used')
    qty_scrapped = fields.Float('Qty scrapped')
    lot_assigned_str = fields.Char('Lot', compute='_get_lot_assigned',
                                   store=True)

    @api.one
    @api.depends('state', 'lot_ids')
    def _get_lot_assigned(self):
        lot_str = ''
        if self.lot_ids:
            print "por lote"
            for lot in self.lot_ids:
                lot_str += lot.name + ','
        else:
            print "por origen"
            origin = self.search([('consumed_for', '=', self.id)])
            self.lot_assigned_str = origin.lot_assigned_str
        if lot_str:
            lot_str = lot_str[:-1]
            self.lot_assigned_str = lot_str
