# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Marcos Ybarra<marcos.ybarra@pharmadus.com>$
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

class partner_review(orm.Model):
    _inherit = 'res.partner'
    _description = "List of partners in Waiting for review state"
    _columns = {
        'confirmed': fields.boolean('Client with data reviewed?'),
    }
    _defaults = {
            'confirmed' : False,
    }

    #Return true if the user is Manager to edit the new client state "Confirmed"
    def _check_permissions(self, cr, uid,  context):
        res = {}
        # Get the PR Manager group id
        manager_id = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'newclient_review',
                                                                          'group_partners_review')[1]

        # Get the user and see what groups he/she is in
        user_obj = self.pool.get('res.users')
        user = user_obj.browse(cr, uid, uid, context=context)

        user_group_ids = []
        for grp in user.groups_id:
            user_group_ids.append(grp.id)

        return (manager_id in user_group_ids)


    def confirm_review(self, cr, uid, ids, context=None):
        return self.write(cr, uid, ids, {'confirmed': True})

    def create(self, cr, uid, vals, context=None):
        if context is None:
            context = {}
        #If partner is added by a Manager or is a supplier... data is always confirmed
        #If us user, or if is a client from prestashop
        ##user assign as creator of the partner TO-DO
        creatorid = self.pool.get('ir.model.data').get_object_reference(cr, uid, 'base', 'user_root')[1]

        obj_user = self.pool.get('res.users')
        list_user = obj_user.search(cr, uid, [('id', '=', creatorid)] )
        size_list_user = len(list_user)

        if (self._check_permissions(cr, uid, context) or vals.get('supplier')==True or
                    context.get('alias_model_name')=='res.users' or context.get('connector_no_export')==True):
            vals['confirmed']=True
            if (context.get('connector_no_export') and (size_list_user==1)): ##It is assigned to a custom user
                vals['user_id']=creatorid
                return super(partner_review, self).create(cr, creatorid, vals, context=context)
        return super(partner_review, self).create(cr, uid, vals, context=context)