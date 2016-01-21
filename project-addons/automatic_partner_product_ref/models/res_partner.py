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
from openerp import models, fields, api
import base_conversion


class ResPartner(models.Model):
    _inherit = 'res.partner'

    reference = fields.Char('Reference',
                            compute='_compute_reference',
                            store=True,
                            readonly=True)

    @api.one
    @api.depends('create_date', 'write_date')
    def _compute_reference(self):
        if not self.reference:
            self.reference = 'E' + base_conversion.baseN(self.id)

    @api.multi
    def write(self, vals):
        if len(self.ids) == 1 and (not self.ref) and not vals.get('ref', False):
            vals['ref'] = vals.get('reference', False) or self.reference
        return super(ResPartner, self).write(vals)
