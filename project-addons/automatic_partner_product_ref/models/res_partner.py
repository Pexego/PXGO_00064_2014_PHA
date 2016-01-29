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
from openerp import models, fields, api, SUPERUSER_ID
import base_conversion


class ResPartner(models.Model):
    _inherit = 'res.partner'

    ref = fields.Char('Contact Reference', select=1, readonly=True)

    def _compute_reference(self):
        if self.ref:
            reference = self.ref
        else:
            reference = base_conversion.baseN(self.id, 36,
                                        'ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789',
                                        4)
            if self.company_id == self.env.ref('base.main_company'):
                reference = 'P' + reference
            elif self.company_id == self.env.ref('__export__.res_company_6'):
                reference = 'ML' + reference
            elif self.company_id == self.env.ref('__export__.res_company_7'):
                reference = 'MR' + reference
            elif self.company_id == self.env.ref('__export__.res_company_5'):
                reference = 'S' + reference
            else:
                reference = '#' + reference
        return reference

    @api.model
    def create(self, vals):
        res = super(ResPartner, self).create(vals)
        if not res.ref:
            res.ref = res._compute_reference()
        return res

    @api.multi
    def write(self, vals):
        if len(self.ids) == 1 and (not self.ref) and not vals.get('ref', False):
            vals['ref'] = self._compute_reference()
        return super(ResPartner, self).write(vals)

    def init(self, cr):
        partner_ids = self.search(cr, SUPERUSER_ID, [('ref', 'in', (False, ''))])
        partners = self.browse(cr, SUPERUSER_ID, partner_ids)
        for p in partners:
            p.ref = p._compute_reference()