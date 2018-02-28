# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    copy_from = fields.Many2one(string='Copy from...', comodel_name='mrp.bom')

    @api.multi
    def action_copy_from(self):
        self.ensure_one()
        if self.copy_from and self.copy_from.bom_line_ids:
            for line in self.copy_from.bom_line_ids:
                new_line = line.copy()
                new_line.bom_id = self.id
        return self
