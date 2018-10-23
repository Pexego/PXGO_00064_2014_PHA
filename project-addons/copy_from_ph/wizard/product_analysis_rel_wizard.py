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
        dest_ids = self.env.context.get('active_ids', False)
        src = self.copy_from
        if src and src.analysis_ids:
            for id in dest_ids:
                self.env['product.template'].browse(id).analysis_ids.unlink()
                for line in self.copy_from.analysis_ids:
                    new_line = line.copy()
                    new_line.product_id = id
                    if line.boolean_selection:
                        new_line.on_change_boolean_selection()
        return self
