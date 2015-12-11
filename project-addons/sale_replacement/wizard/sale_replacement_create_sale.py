# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, exceptions, _
from datetime import date


class SaleReplacementCreateSale(models.TransientModel):

    _name = 'sale.replacement.create.sale'

    @api.multi
    def create_sale(self):
        model = self.env.context.get('active_model', False)
        line_ids = self.env.context.get('active_ids', False)
        partner_dct = self.env[model].read_group([('id', 'in', line_ids)], ['partner_id'], ['partner_id'])
        partner_ids = [x['partner_id'][0] for x in partner_dct]
        for partner in self.env['res.partner'].browse(partner_ids):
            lines = self.env[model].search([('partner_id', '=', partner.id), ('id', 'in', line_ids)])
            sale_lines = []
            for line in lines:
                line_vals = {
                    'product_id': line.product_id.id,
                    'replacement': True,
                    'orig_sale': line.order_id.id,
                    'product_uom_qty': line.quantity - line.quantity_invoiced,
                }
                line_default = self.env['sale.order.line'].default_get(['product_uom', 'state'])
                line_vals.update(line_default)
                sale_lines.append((0, 0, line_vals))

        act = self.env.ref('sale.action_orders')
        res = act.read()[0]
        res['views'] = [(self.env.ref('sale.view_order_form').id or False, 'form')]
        res['context'] = {'default_partner_id': partner.id, 'order_line': str(sale_lines)}
        return res
