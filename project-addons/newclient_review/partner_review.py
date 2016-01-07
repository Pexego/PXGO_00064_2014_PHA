# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
#    $Marcos Ybarra<marcos.ybarra@pharmadus.com>$
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

from openerp import models, fields, api
from openerp.tools.translate import _
import sys


class PartnerReview(models.Model):
    _inherit = 'res.partner'
    _description = 'List of partners in Waiting for review state'

    confirmed = fields.Boolean('Client with data reviewed?', defaul=False)

    # Return true if the user is Manager to edit the new client state "Confirmed"
    def _check_permissions(self):
        # Get the PR Manager group id
        manager_group_id = self.env.ref('newclient_review.group_partners_review')
        return self.env.user in manager_group_id.users

    @api.multi
    def confirm_review(self):
        self.confirmed = True
        return True

    @api.model
    def create(self, vals):
        # If partner is added by a Manager or is a supplier... data is always confirmed
        # TODO: PRESTASHOP -> If is a user or a client from prestashop
        # TODO: PRESTASHOP -> assign user as creator of the partner
        vals['confirmed'] = self._check_permissions() or vals.get('supplier')
        return super(PartnerReview, self).create(vals)

    @api.multi
    def write(self, vals):
        vals['confirmed'] = self._check_permissions()

        attrs = self.fields_get()
        for partner in self:
            fields = ''
            for field in vals:
                if field != 'confirmed':
                    original_value = eval('partner.' + field)
                    original_value = original_value if original_value \
                                                    else _('(empty)')
                    fields += u'<br>{0}: {1} => {2}'.format(
                            _(attrs[field]['string']), original_value, vals[field])

                partner.message_post(body=_('Modified fields: ') + fields)

        return super(PartnerReview, self).write(vals)