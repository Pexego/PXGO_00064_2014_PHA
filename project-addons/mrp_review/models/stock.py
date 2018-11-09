# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class StockMove(models.Model):

    _inherit = 'stock.move'

    @api.multi
    def action_cancel(self):
        """
            Evitamos la cancelacion de movimientos al hacer el release all
        """
        if not self._context.get('not_cancel'):
            return super(StockMove, self).action_cancel()
