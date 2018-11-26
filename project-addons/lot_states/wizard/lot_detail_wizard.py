# -*- coding: utf-8 -*-
# © 2014 Pexego
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp


class StockLotDetailWizard(models.TransientModel):
    _name = 'stock.lot.detail.wizard'

    lot_id = fields.Many2one(comodel_name='stock.production.lot', readonly=True)
    total = fields.Float(digits=dp.get_precision('Product Unit of Measure'),
                         readonly=True)
    approved = fields.Float(digits=dp.get_precision('Product Unit of Measure'),
                            readonly=True)
    rejected = fields.Float(digits=dp.get_precision('Product Unit of Measure'),
                            readonly=True)
    remaining = fields.Float(digits=dp.get_precision('Product Unit of Measure'),
                             readonly=True)
    detail_ids = fields.One2many(related='lot_id.detail_ids')

    @api.model
    def create(self, vals):
        lot_id = vals.get('lot_id', False)
        if lot_id:
            quant_ids = self.env['stock.quant'].search([('lot_id', '=', lot_id),
                                        ('location_id.usage', '=', 'internal')])
            total = 0
            for quant in quant_ids:
                total += quant.qty

            wh = self.env['stock.warehouse'].search(
                [('company_id', '=', self.env.user.company_id.id)])
            quant_ids = self.env['stock.quant'].search([
                ('lot_id', '=', lot_id),
                ('location_id.id', 'child_of', wh.wh_qc_stock_loc_id.id)
            ])
            remaining = 0
            for quant in quant_ids:
                remaining += quant.qty

            approved = 0
            rejected = 0
            lot_id = self.env['stock.production.lot'].browse(lot_id)
            for detail in lot_id.detail_ids:
                if detail.state == 'approved':
                    approved += detail.quantity
                else:
                    rejected += detail.quantity

            vals['total'] = total
            vals['approved'] = approved
            vals['rejected'] = rejected
            vals['remaining'] = remaining
        return super(models.TransientModel, self).create(vals)

    @api.multi
    def button_approve(self):
        self.lot_id.action_approve()

    @api.multi
    def button_fill_by_moves(self):
        wh = self.env['stock.warehouse'].search(
            [('company_id', '=', self.env.user.company_id.id)])
        approved_move_ids = self.env['stock.move'].search([
            ('id', 'in', self.lot_id.move_related_ids.ids),
            ('state', '=', 'done'),
            ('location_id', 'child_of', wh.wh_qc_stock_loc_id.id),
            ('location_dest_id.usage', '=', 'internal'),
            ('location_dest_id', 'child_of', wh.lot_stock_id.id),
        ])
        rejected_move_ids = self.env['stock.move'].search([
            ('id', 'in', self.lot_id.move_related_ids.ids),
            ('state', '=', 'done'),
            ('location_id', 'child_of', wh.wh_qc_stock_loc_id.id),
            ('location_dest_id.usage', '=', 'internal'),
            '!',
            ('location_dest_id', 'child_of', wh.lot_stock_id.id),
        ])
        detail_ids = [(5, 0, 0)]  # To clear all previous existing details
        for m in approved_move_ids:
            detail_ids += [(0, 0, {
                'date': m.date,
                'state': 'approved',
                'quantity': sum(m.quant_ids.
                            filtered(lambda q: q.lot_id == self.lot_id).
                            mapped('qty'))
            })]
        for m in rejected_move_ids:
            detail_ids += [(0, 0, {
                'date': m.date,
                'state': 'rejected',
                'quantity': sum(m.quant_ids.
                            filtered(lambda q: q.lot_id == self.lot_id).
                            mapped('qty'))
            })]
        self.lot_id.write({'detail_ids': detail_ids})

        # Re-create wizard to recompute all
        wizard_id = self.env['stock.lot.detail.wizard']. \
            create({'lot_id': self.lot_id.id})
        view = self.env.ref('lot_states.stock_lot_details_form')
        return {
            'name': _('Lot details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.lot.detail.wizard',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': wizard_id.id,
        }