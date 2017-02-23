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
from openerp import models, fields


class SaleOrder(models.Model):

    _inherit = "sale.order"

    urgent = fields.Boolean("Urgent")
    top_date = fields.Date("Limit date")
    delivery_date = fields.Date()
    season = fields.Char()
    customer_branch = fields.Char()
    customer_department = fields.Char()
    customer_transmitter = fields.Many2one('res.partner')

class SaleOrderLine(models.Model):

    _inherit = 'sale.order.line'

    units_per_package = fields.Integer()
