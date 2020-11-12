# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockPickingSpecial(models.TransientModel):
    _name = 'stock.picking.special'
    _inherits = {'stock.picking': 'picking_id'}

    picking_id = fields.Many2one(comodel_name='stock.picking',
                                 required=True, ondelete='cascade')
    aux_partner_id = fields.Many2one(comodel_name='res.partner',
                                     string='Empresa')
    aux_owner_id = fields.Many2one(comodel_name='res.partner',
                                   string='Propietario')

    @api.multi
    def write(self, vals):
        self.ensure_one()
        data = {}
        if 'aux_partner_id' in vals:
            data['partner_id'] = vals['aux_partner_id']
            data['owner_id']   = vals['aux_owner_id']
        self.picking_id.write(data)
        res = super(StockPickingSpecial, self).write(vals)
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def call_special_form(self):
        rec = self.env['stock.picking.special'].create({
            'picking_id':     self.id,
            'aux_partner_id': self.partner_id.id,
            'aux_owner_id':   self.owner_id.id
        })
        view_id = self.env.ref('custom_views.view_stock_picking_special_form')

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking.special',
            'view_id': view_id.id,
            'res_id': rec.id,
            'target': 'current'
        }
