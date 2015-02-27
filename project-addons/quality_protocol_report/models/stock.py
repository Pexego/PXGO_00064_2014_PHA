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
from openerp import models, fields, api, exceptions, _


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
    @api.depends('state', 'lot_ids', 'move_orig_ids.state', 'move_orig_ids.lot_ids')
    def _get_lot_assigned(self):
        lot_str = ''
        if self.lot_ids:
            for lot in self.lot_ids:
                lot_str += lot.name + ','
        else:
            original_lots = ''
            for origin in self.move_orig_ids:
                if origin.lot_assigned_str:
                    original_lots += origin.lot_assigned_str + ','
            if original_lots:
                original_lots = original_lots[:-1]
            self.lot_assigned_str = original_lots
        if lot_str:
            lot_str = lot_str[:-1]
            self.lot_assigned_str = lot_str

class stockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.multi
    def do_enter_transfer_details(self):
        """Se hereda la función sobreescrita en mrp_return_moves"""
        docs_no_submited = []
        for move in self.move_lines:
            if move.move_dest_id and move.move_dest_id.raw_material_production_id:
                for wkcenter_line in move.move_dest_id.raw_material_production_id.workcenter_lines:
                    if not wkcenter_line.workcenter_id.protocol_type_id.is_hoard:
                        continue
                    if not wkcenter_line.doc_submited:
                        if wkcenter_line.workcenter_id.name not in docs_no_submited:
                            docs_no_submited.append(wkcenter_line.workcenter_id.name)
        if docs_no_submited:
            raise exceptions.Warning(_('Document error'), _('Documents not submited: \n %s') % (','.join(docs_no_submited)))
        return super(stockPicking, self).do_enter_transfer_details()
