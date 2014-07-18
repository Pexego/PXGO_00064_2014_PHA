# -*- coding: utf-8 -*-
# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Marcos Ybarra Mayor <marcos.ybarra@pharmadus.com>$
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
from openerp.osv import orm, fields, osv
from openerp import tools
from openerp.tools.translate import _

class Partner_review(orm.Model):
    _inherit = 'res.partner'
    _description = "List of partners in Waiting for review state"
    _columns = {
        'confirmed': fields.boolean('Cliente con datos revisados?'),
    }
    _defaults = {
            'confirmed' : False,
    }

    #Return true if the user is Manager to edit the new client state "Confirmed"
    def _check_permissions(self, cr, uid,  context):
        res = {}
        # Get the PR Manager id's
        group_obj = self.pool.get('res.groups')
        manager_ids = group_obj.search(cr, uid, [('name','=', 'PR/Manager')])

        # Get the user and see what groups he/she is in
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)

        user_group_ids = []
        for grp in user.groups_id:
            user_group_ids.append(grp.id)

        if ( manager_ids[0] in user_group_ids):
            # 'Manager'
            return True
        else:
            # = 'User'
            return False


    def confirm_review(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'confirmed': True})

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        if (self._check_permissions(cr, uid, context)):
            vals['confirmed']=True
         #Show popup message
        #else:
            #self.message_post(cr, uid, False, body=_("New Question has been <b>created</b>"), context=context)
        return super(Partner_review, self).create(cr, uid, vals, context=context)