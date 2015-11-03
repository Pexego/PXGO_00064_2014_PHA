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


class CrmClaimDepartmentType(models.Model):

    _name = 'crm.claim.department.type'
    name = fields.Char('Name', required=True)
    department_id = fields.Many2one('hr.department', 'Department')

class CrmClaim(models.Model):

    _inherit = 'crm.claim'

    department_type = fields.Many2one('crm.claim.department.type', 'Type')

    @api.model
    def create(self, vals):
        import ipdb; ipdb.set_trace()
        if vals.get('department_type'):
            department_type = self.env['crm.claim.department.type'].browse(vals['department_type'])
            manager = department_type.department_id.manager_id.user_id.partner_id
            if type(vals.get('message_follower_ids', False)) == type(False):
                vals['message_follower_ids'] = []
            message_follower_ids = [(4, manager.id)] + vals.get('message_follower_ids', [])
            vals['message_follower_ids'] = message_follower_ids
        return super(CrmClaim, self).create(vals)
