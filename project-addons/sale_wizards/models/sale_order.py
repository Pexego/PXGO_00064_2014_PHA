# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def from_line_subline(self):
        wizard_id = self.env['sale.from.line.subline'].create({
            'sale_order_id': self.id
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale from line subline wizard',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.from.line.subline.items',
            'domain': [('wizard_id', '=', wizard_id.id)],
            'view_id': self.env.ref('sale_wizards.sale_from_line_subline_wizard').id,
            'search_view_id': self.env.
                ref('sale_wizards.sale_from_line_subline_search').id,
            'context': {
                'search_default_group_by_line': 1,
            },
            'target': 'new',
        }

    @api.multi
    def from_history(self):
        wizard_id = self.env['sale.from.history'].create({
            'sale_order_id': self.id
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale from history wizard',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.from.history.items',
            'domain': [('wizard_id', '=', wizard_id.id)],
            'view_id': self.env.ref('sale_wizards.sale_from_history_wizard').id,
            'target': 'current',
        }
