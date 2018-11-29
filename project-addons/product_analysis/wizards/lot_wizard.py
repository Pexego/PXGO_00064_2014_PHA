# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockProductionLotSelect(models.TransientModel):
    _name = 'stock.production.lot.select'

    dest_lot_id = fields.Many2one(comodel_name='stock.production.lot',
        string='Lot',
        readonly=True)
    dest_product_id = fields.Many2one(related='dest_lot_id.product_id',
                                      readonly=True)
    lot_id = fields.Many2one(comodel_name='stock.production.lot',
        string='Lot')
    product_id = fields.Many2one(related='lot_id.product_id', readonly=True)

    @api.multi
    def action_select_lot(self):
        self.ensure_one()
        self.dest_lot_id.copy_analysis_results(self.lot_id)
        return True