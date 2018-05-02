# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    sale_channel_id = fields.Many2one(string='Canal de venta',
                                      comodel_name='sale.channel',
                                      compute='_compute_sale_channel',
                                      search='_search_sale_channel')

    @api.one
    @api.depends('sale_id', 'sale_id.sale_channel_id')
    def _compute_sale_channel(self):
        self.sale_channel_id = self.sale_id.sale_channel_id

    def _search_sale_channel(self, operator, value):
        sale_ids = self.env['sale.order'].search([
            ('sale_channel_id', operator, value),
            ('procurement_group_id', '!=', False)
        ])
        procurement_group_ids = [s.procurement_group_id.id for s in sale_ids]
        picking_ids = self.env['stock.picking'].search([
            ('group_id', 'in', procurement_group_ids)
        ])
        return [('id', 'in', [p.id for p in picking_ids])]
