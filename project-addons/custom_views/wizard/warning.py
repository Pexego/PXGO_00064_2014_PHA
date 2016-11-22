# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
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


class CustomViewsWarning(models.TransientModel):
    _name = 'custom.views.warning'

    message = fields.Text('Message')

    def show_message(self, title='Warning message', message_text='No message!'):
        warning = self.create({'message': message_text})
        view = self.env.ref('custom_views.custom_views_warning_form')
        return {
            'name': title,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'custom.views.warning',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': warning.id,
            'context': self.env.context,
        }