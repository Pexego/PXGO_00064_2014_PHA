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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api

class res_partner(models.Model):
    _inherit = 'res.partner'

    @api.multi
    def name_get(self):
        key = 'concatenate_name_comercial'

        if key in self._context and self._context.get(key): # If key is defined and form is in create mode
            res = []
            for rec in self:
                name = rec.name + (' (' + rec.comercial + ')' if rec.comercial else '')
                res.append((rec.id, name))
            return res
        else:
            return super(res_partner, self).name_get()
