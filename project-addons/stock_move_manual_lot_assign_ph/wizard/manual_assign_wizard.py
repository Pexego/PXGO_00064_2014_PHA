# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round


class StockMoveAssignManualLot(models.TransientModel):
    _inherit = 'stock.move.assign.manual.lot'

    @api.multi
    @api.constrains('line_ids')
    def check_qty(self):
        if not self.env.context.get('compute_only', False):
            super(StockMoveAssignManualLot, self).check_qty()