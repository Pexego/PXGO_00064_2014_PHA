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
        for key in vals:
            data[key.replace('aux_', '')] = vals[key]
        self.picking_id.write(data)
        res = super(StockPickingSpecial, self).write(vals)
        return res


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def call_special_form(self):
        wizard = self.env['stock.picking.special']
        data = {'picking_id': self.id}
        for column in wizard._columns:
            if column[:4] == 'aux_':
                if wizard._columns[column]._type == 'many2one':
                    data[column] = eval('self.' + column[4:] + '.id')
                else:
                    data[column] = eval('self.' + column[4:])
        rec = wizard.create(data)
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
