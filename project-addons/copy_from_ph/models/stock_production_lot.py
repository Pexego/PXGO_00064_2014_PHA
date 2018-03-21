# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    sequence_id = fields.Many2one(comodel_name='ir.sequence',
                                  related='product_id.sequence_id')
    copy_analysis_from = fields.Many2one(string='Copy from...',
            comodel_name='stock.production.lot')
    copy_analysis_from_product_id = fields.Many2one(
        comodel_name="product.product",
        related="copy_analysis_from.product_id")

    @api.multi
    def action_copy_analysis_from(self):
        self.ensure_one()
        excluded_fields = ('create_date', 'create_uid', 'display_name', 'id',
                           'lot_id', '__last_update', 'write_date', 'write_uid')
        if self.copy_analysis_from and self.copy_analysis_from.analysis_ids:
            for line in self.copy_analysis_from.analysis_ids:
                analysis_id = self.analysis_ids.\
                    filtered(lambda r: r.analysis_id == line.analysis_id)
                if analysis_id:
                    dict = {}
                    for field in line._fields:
                        if field not in excluded_fields:
                            dict[field] = getattr(line, field)
                    analysis_id.update(dict)
        return self
