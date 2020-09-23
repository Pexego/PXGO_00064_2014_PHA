# -*- coding: utf-8 -*-
# © 2015 Comunitea
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    stock_url = fields.Char('Stock url', compute='_get_stock_url')
    qty_available = fields.Float('Quantity On Hand',
                                 related='product_id.qty_available',
                                 readonly=True,
                                 digits=(16, 2))
    virtual_available = fields.Float('Virtual Available',
                                     related='product_id.virtual_available',
                                     readonly=True,
                                     digits=(16, 2))
    virtual_conservative = fields.Float('Virtual stock conservative',
                                     related='product_id.virtual_conservative',
                                     readonly=True,
                                     digits=(16, 2))
    packing = fields.Float(string='Packing',
                           related='product_id.packing',
                           readonly=True,
                           digits=(16, 2))
    box_elements = fields.Float(string='Box elements',
                                related='product_id.box_elements',
                                readonly=True,
                                digits=(16, 2))

    @api.one
    @api.depends('product_id')
    def _get_stock_url(self):
        if self.product_id:
            action_id = self.env.ref('stock.product_open_quants').id
            self.stock_url = '/web#page=0&limit=&view_type=list&model=' \
                             'stock.quant&action=%s&active_id=%s' % \
                (action_id, self.product_id.id)
