# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ProductProduct(models.Model):
    _inherit = 'product.product'

    copy_analysis_from = fields.Many2one(string='Copy from...',
                                         comodel_name='product.product')

    @api.multi
    def action_copy_analysis_from(self):
        self.ensure_one()
        if self.copy_analysis_from and self.copy_analysis_from.analysis_ids:
            for line in self.copy_analysis_from.analysis_ids:
                new_line = line.copy()
                new_line.product_id = self.id
        return self
