# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, exceptions, _
import uuid


class ir_ui_view(models.Model):

    _inherit = 'ir.ui.view'

    @api.multi
    def assign_id(self):
        self.ensure_one()
        model_data = self.env['ir.model.data'].create(
            {'module': 'False', 'name': str(uuid.uuid4()).replace('-', ''),
             'model': 'ir.ui.view', 'res_id': self.id})
        self.arch = '<?xml version="1.0"?>\n<t name="%s" \
t-name="%s">\n%s\n</t>' % (self.name, model_data.complete_name, self.arch)
