# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ProductAnalysisRelWizard(models.TransientModel):
    _name = 'product.analysis.rel.wizard'

    copy_from = fields.Many2one(string='Copy from...',
                                comodel_name='product.template')

    @api.multi
    def action_copy_from(self):
        fields_to_copy = ('method', 'analysis_type', 'boolean_selection',
                          'expected_result_expr', 'decimal_precision')
        dest_ids = self.env.context.get('active_ids', False)
        src = self.copy_from
        if src and src.analysis_ids:
            for id in dest_ids:
                dest = self.env['product.template'].browse(id)
                for line in src.analysis_ids:
                    analysis_id = dest.analysis_ids.filtered(
                        lambda r: r.analysis_id == line.analysis_id)
                    if analysis_id:
                        dict = {}
                        for field in line._fields:
                            if field in fields_to_copy:
                                dict[field] = getattr(line, field)
                        analysis_id.update(dict)
        return self
