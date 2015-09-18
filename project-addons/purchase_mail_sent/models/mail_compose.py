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
from openerp.osv import orm, fields, osv

class mail_compose_message(osv.Model):
    _inherit = 'mail.compose.message'

    def send_mail(self, cr, uid, ids, context=None):
        context = context or {}
        if context.get('default_model') == 'purchase.order' and context.get('default_res_id'):
            context = dict(context, mail_post_autofollow=True)
            vari = self.pool.get('purchase.order')
            vari.signal_workflow(cr, uid, [context['default_res_id']], 'send_rfq')
            if vari.browse(cr, uid, [context['default_res_id']]).state == 'approved':
                vari.write(cr, uid, [context['default_res_id']], {'pc_sent': True})
        return super(mail_compose_message, self).send_mail(cr, uid, ids, context=context)