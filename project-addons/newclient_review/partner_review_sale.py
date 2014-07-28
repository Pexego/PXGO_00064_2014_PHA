# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Marcos Ybarra <marcos.ybarra@pharmadus.com>$
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
from openerp.osv import osv
from openerp.tools.translate import _

class partner_review_sale(models.Model):
    _inherit = 'sale.order'

    def action_button_confirm(self, cr, uid, ids, context=None):
         #If client data is not confirmed, sale cant be done
        sale = self.browse(cr,uid,ids,context=None)
        partner_objt = sale.partner_id
        if (not partner_objt.confirmed):
            #Show message and rollback
            raise osv.except_osv(_('Error'), _('Client without review. A manager must review data to confirm it before confirm order, you can "Save" this order to confirm later.'))
        return super(partner_review_sale, self).action_button_confirm(cr, uid, ids, context=context)