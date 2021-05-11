# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    sequence_id = fields.Many2one(comodel_name='ir.sequence',
                                  related='product_id.sequence_id',
                                  readonly=True)
    copy_analysis_from = fields.Many2one(string='Copy from...',
            comodel_name='stock.production.lot')
    copy_analysis_from_product_id = fields.Many2one(
        comodel_name="product.product",
        related="copy_analysis_from.product_id",
        readonly=True)

    @api.multi
    def action_copy_analysis_from(self):
        fields_to_copy = ('num_container_sample_proposed',
                          'num_container_sample_to_do',
                          'num_container_sample_realized',
                          'num_sampling_proposed',
                          'num_sampling_to_do',
                          'num_sampling_realized',
                          'sampling_type',
                          'sampling_notes',
                          'sampling_date',
                          'sampling_realized',
                          'analysis_notes',
                          'revised_by',
                          'notes')
        excluded_fields = ('create_date', 'create_uid', 'display_name', 'id',
                       'lot_id', '__last_update', 'write_date', 'write_uid')

        for lot in self:
            if lot.copy_analysis_from:
                origin = lot.copy_analysis_from
                dict = {}
                for field in fields_to_copy:
                    if field in origin._fields:
                        dict[field] = getattr(origin, field)
                lot.update(dict)

                if lot.copy_analysis_from.analysis_ids:
                    for line in lot.copy_analysis_from.analysis_ids:
                        analysis_id = lot.analysis_ids.\
                            filtered(lambda r: r.analysis_id == line.analysis_id)
                        if analysis_id:
                            dict = {}
                            for field in line._fields:
                                if field not in excluded_fields:
                                    dict[field] = getattr(line, field)
                            analysis_id.update(dict)
        return self

    @api.multi
    def action_copy_analysis_to(self):
        rec_id = self.env['lot.copy.analysis.to.wizard'].\
            create({'origin_lot_id': self.id})
        wizard_id = self.env.ref('copy_from_ph.lot_copy_analysis_to_wizard')
        return {
            'name': _(
                'Lots to which the analysis parameters are to be copied'),
            'type': 'ir.actions.act_window',
            'view_type': 'tree',
            'view_mode': 'form',
            'res_model': 'lot.copy.analysis.to.wizard',
            'views': [(wizard_id.id, 'form')],
            'view_id': wizard_id.id,
            'res_id': rec_id.id,
            'target': 'new',
        }