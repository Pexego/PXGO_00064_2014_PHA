# -*- coding: utf-8 -*-
# © 2014 Pexego
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
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
