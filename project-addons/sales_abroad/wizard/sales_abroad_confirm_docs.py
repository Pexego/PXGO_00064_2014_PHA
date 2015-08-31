# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
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
##############################################################################
#

from openerp import models, fields, api, _


class sales_abroad_confirm_docs(models.TransientModel):
    _name = 'sales.abroad.confirm.docs'
    _inherits = {'res.country': 'country_id'}

    country_id = fields.Many2one('res.country', 'Country', required=True, ondelete='cascade')
    reference = fields.Char()

    @api.multi
    def wizard_view(self, country, reference):
        view = self.env.ref('sales_abroad.view_sales_abroad_confirm_docs')
        current = self.create({'country_id': country, 'reference': reference})

        return {
            'name': _('Sales abroad documents'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': current.ids[0],
            'context': self.env.context,
        }

    @api.one
    def action_confirmed(self):
        ctx = self.env.context
        self.env[ctx['active_model']].browse(ctx['active_ids']).write({'docs_confirmed': True})