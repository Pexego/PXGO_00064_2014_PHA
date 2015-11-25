# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models, api, exceptions
from openerp.tools.translate import _


class ResPartner(models.Model):
    _inherit = 'res.partner'

    pre_customer = fields.Boolean('pre-Customer', default=False)

    @api.multi
    def validate_customer(self):
        warning = ''

        if not (self.street and self.street.strip()):
            warning += _('- Street field is mandatory.\n')
        if not self.zip_id:
            warning += _('- Must select a postal code/city option.\n')
        if not (self.zip and self.zip.strip()):
            warning += _('- Zip field is mandatory.\n')
        if not (self.city and self.city.strip()):
            warning += _('- City field is mandatory.\n')
        if not self.state_id:
            warning += _('- Must select a State.\n')
        if not self.country_id:
            warning += _('- Must select a Country.\n')
        if not (self.phone and self.phone.strip()):
            warning += _('- Phone field is mandatory.\n')
        if not (self.vat and self.vat.strip()):
            warning += _('- VAT field is mandatory.\n')

        if warning == '':
            self.pre_customer = False
            return {
                'type': 'ir.actions.act_window',
                'view_type': 'form',
                'view_mode': 'form',
                'res_model': 'res.partner',
                'view_id': self.env.ref('base.view_partner_form').id,
                'res_id': self.id,
                'target': 'current'
            }
        else:
            raise exceptions.Warning(_('Error validating the customer:\n'),
                                     warning)
            return False
