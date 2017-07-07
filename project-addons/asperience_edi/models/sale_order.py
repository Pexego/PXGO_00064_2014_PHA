# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
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
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class SaleOrder(models.Model):

    _inherit = "sale.order"

    urgent = fields.Boolean("Urgent")
    top_date = fields.Date("Limit date")
    delivery_date = fields.Date()
    season = fields.Char()
    customer_branch = fields.Char()
    customer_department = fields.Char()
    customer_transmitter = fields.Many2one('res.partner')
    customer_transmitter = fields.Many2one('res.partner')
    total_packages = fields.Integer()

    @api.multi
    def print_eci_report(self):
        self.ensure_one()
        custom_data = {
            'sale_id': self.id,
        }
        rep_name = 'asperience_edi.eci_order_report'
        rep_action = self.env["report"].get_action(self, rep_name)
        rep_action['data'] = custom_data
        return rep_action


class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    units_per_package = fields.Integer()
    brut_price = fields.Float('Brut Price',
                              digits_compute=dp.
                              get_precision('Product Price'))
    net_price = fields.Float('Net Price',
                              digits_compute=dp.
                              get_precision('Product Price'))
