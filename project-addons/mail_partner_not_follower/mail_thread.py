# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
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

from openerp.addons.mail.mail_thread import mail_thread

message_subscribe_orig = mail_thread.message_subscribe

def message_subscribe(self, cr, uid, ids, partner_ids, subtype_ids=None,
                      context=None):
    # Remove customer/supplier partner_ids
    model = self._name
    if model in ['sale.order', 'purchase.order', 'account.invoice']:
        for rec in self.pool.get(model).browse(cr, uid, ids):
            partner_id = rec.partner_id.id
            while partner_id in partner_ids:
                partner_ids.remove(partner_id)

    # Call original method with overwritten parameter
    return message_subscribe_orig(self, cr, uid, ids, partner_ids,
                                 subtype_ids=subtype_ids, context=context)

# Install override
mail_thread.message_subscribe = message_subscribe