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
        for analysis_rel_id in self.dest_lot_id.analysis_ids.\
                filtered('raw_material_analysis'):
            copy_analysis_id = self.lot_id.analysis_ids.filtered(
                lambda r: r.analysis_id.id == analysis_rel_id.analysis_id.id)
            if copy_analysis_id:
                analysis_rel_id.unlink()
                copy_analysis_id.copy(default={'lot_id': self.dest_lot_id.id,
                                               'raw_material_analysis': True})
        return True