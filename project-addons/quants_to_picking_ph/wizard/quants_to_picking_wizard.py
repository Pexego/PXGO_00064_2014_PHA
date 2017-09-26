# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _


class QuantsToPickingWizard(models.TransientModel):
    _name = 'quants.to.picking.wizard'

    picking_id = fields.Many2one(comodel_name='stock.picking')
    location_dest_id = fields.Many2one(comodel_name='stock.location',
                                       string='Destination location')

    @api.multi
    def set_dest_location(self):
        self.picking_id.move_lines.write({
            'location_dest_id': self.location_dest_id.id
        })

        return {
            'name': _('Picking from quants'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'type': 'ir.actions.act_window',
            'target': 'current',
            'res_id': self.picking_id.id,
            'context': {},
        }