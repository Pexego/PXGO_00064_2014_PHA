# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
#    $Marcos Ybarra <marcos.ybarra@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, api, fields, _

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    @api.depends('partner_id')
    def onchange_partner_id(self, part):
        res = super(SaleOrder, self).onchange_partner_id(part)

        salesmangroup_id = self.env.ref('custom_permissions.group_salesman_ph')
        if self.env.user in salesmangroup_id.users:
            res['value']['sale_channel_id'] = salesmangroup_id.default_sale_channel

        return res
