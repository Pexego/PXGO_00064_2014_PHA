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

    is_in_group_salesmanph = fields.Boolean(
        string='is in group salesmanph',
        compute='_is_in_group_salesman',
        help='User is in SalesmanPH group',
        store=False)

    @api.multi
    @api.depends('name')
    def _is_in_group_salesman(self):
        # Get the SalesmanPh Manager group id
        salesmangroup_id = self.env['ir.model.data'].get_object_reference('custom_permissions',
                                                                          'group_salesman_ph')[1]

        # Get the user and see what groups he/she is in
        user_obj = self.env['res.users']
        user = user_obj.browse(self._uid)

        user_group_ids = []
        for grp in user.groups_id:
            user_group_ids.append(grp.id)
        returnacion = (salesmangroup_id in user_group_ids)
        self.is_in_group_salesmanph = returnacion

    def _is_in_group_salesman_bis(self):
        # Get the SalesmanPh Manager group id
        salesmangroup_id = self.env['ir.model.data'].get_object_reference('custom_permissions',
                                                                          'group_salesman_ph')[1]

        # Get the user and see what groups he/she is in
        user_obj = self.env['res.users']
        user = user_obj.browse(self._uid)

        user_group_ids = []
        for grp in user.groups_id:
            user_group_ids.append(grp.id)
        returnacion = (salesmangroup_id in user_group_ids)
        return returnacion
