# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class MrpSetFinalQuantity(models.TransientModel):

    _name = 'mrp.set.final.quantity'

    number_of_cases = fields.Float()
    number_of_infusions = fields.Float()

    @api.multi
    def release(self):
        production = self.env['mrp.production'].browse(
            self._context.get('active_id'))
        if self.number_of_cases:
            production.final_qty = self.number_of_cases
        else:
            cases_quantity = self.number_of_infusions / \
                production.product_id.qty
            production.final_qty = cases_quantity * \
                (1 - production.routing_id.decrease_percentage / 100)
        production.signal_workflow('button_final_qty')
