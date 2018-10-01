# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ProductIncomingParameters(models.TransientModel):
    _name = 'product.incoming.parameters'

    date_start = fields.Date(default='2016-01-01', required=True)
    date_end = fields.Date(default=fields.Date.today(), required=True)

    @api.multi
    def show_product_incoming(self):
        ctx = self.env.context.copy()
        ctx['date_start'] = self.date_start
        ctx['date_end'] = self.date_end

        return {
            'name': 'Products incoming',
            'type': 'ir.actions.act_window',
            'res_model': 'product.incoming',
            'view_type': 'form',
            'view_mode': 'tree',
            'target': 'current',
            'domain': [('data_uid', '=', self.env.user.id)],
            'context': ctx
        }