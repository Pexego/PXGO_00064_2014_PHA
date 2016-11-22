# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
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
from openerp import models, fields, api, SUPERUSER_ID, _


class StockMove(models.Model):
    _inherit = 'stock.move'

    lots_string = fields.Char(string='Lots', readonly=True, index=True)

    @api.multi
    def _get_related_lots_str(self):
        for move in self:
            lot_str = u", ".join([x.name for x in move.lot_ids])
            if move.lots_string != lot_str:
                move.lots_string = lot_str

    @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        for move in self:
            if len(move.lot_ids) > 0:
                self._get_related_lots_str()
        return res

    def init(self, cr):
        move_ids = self.search(cr, SUPERUSER_ID,
                               [('lots_string', 'in', (False, ''))])
        moves = self.browse(cr, SUPERUSER_ID, move_ids)
        moves._get_related_lots_str()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    address_city = fields.Char(related='partner_id.city', store=True)
    address_zip = fields.Char(related='partner_id.zip', store=True)
    address_country = fields.Char(related='partner_id.country_id.name', store=True)
    picking_type_desc = fields.Char(compute='_compute_picking_type_desc')

    @api.one
    @api.depends('picking_type_id')
    def _compute_picking_type_desc(self):
        types = {'outgoing': ' - (Albarán de salida)',
                 'incoming': ' - (Albarán de entrada)',
                 'internal': ' - (Albarán interno)'}
        self.picking_type_desc = types.get(self.picking_type_id.code, '')

    @api.multi
    def _check_reserved_quantities(self):
        unmatched_quantities_found = False
        for picking in self:
            for move in picking.move_lines:
                unmatched_quantities_found = unmatched_quantities_found or \
                    move.partially_available
                if not unmatched_quantities_found:
                    sum = 0
                    for quant in move.reserved_quant_ids:
                        sum += quant.qty
                    unmatched_quantities_found = (sum not in (0, move.product_qty))

        if unmatched_quantities_found:
            return self.env['custom.views.warning'].show_message(
                _('Stock assignment warning'),
                _('WARNING: There are stock reservations that do not match!')
            )
        return True

    @api.multi
    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        return self._check_reserved_quantities() if res else res

    @api.multi
    def rereserve_pick(self):
        super(StockPicking, self).rereserve_pick()
        return self._check_reserved_quantities()

    @api.multi
    def confirm_action_cancel(self):
        view = self.env.ref('custom_views.custom_views_picking_cancel_confirm_form')
        return {
            'name': _('Confirm picking cancellation'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }


class StockHistory(models.Model):
    _inherit = 'stock.history'

    categ_ids = fields.Many2many(related='product_id.categ_ids')