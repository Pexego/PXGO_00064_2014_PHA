# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
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


class QualityProcedure(models.Model):

    _name = "quality.procedure"

    name = fields.Char('Name', size=256, required=True)
    code = fields.Char('Code', size=36, required=True)
    edition = fields.Char('Edition', size=12, required=True)

    def name_get(self, cr, uid, ids, context=None):
        res = []
        for proc in self.browse(cr, uid, ids, context=context):
            name = proc.code + " Ed: " + proc.edition
            res.append((proc.id, name))
        return res
