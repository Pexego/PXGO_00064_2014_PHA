# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import ast


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    issue_count = fields.Integer('Issue count', compute='_get_issue_count')

    @api.one
    def _get_issue_count(self):
        self.issue_count = self.env['crm.claim'].\
            search_count([('lot_id', '=', self.id)])
