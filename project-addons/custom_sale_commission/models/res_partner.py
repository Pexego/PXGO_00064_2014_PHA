# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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


class res_partner(models.Model):

    _inherit = 'res.partner'

    @api.one
    def assign_agent(self):
        self.commission_ids.filtered(lambda x: x.auto).unlink()
        if not self.zip_id or not self.zip_id.agent_ids or not self.category_id:
            return
        for agent in self.zip_id.agent_ids:
            all_categ = self.env['res.partner.category'].search([('id', 'child_of', agent.category_id._ids)])
            if all_categ & self.category_id:
                self.user_id = agent.agent_id.get_user()


class res_partner_agent(models.Model):

    _inherit = 'res.partner.agent'

    auto = fields.Boolean('Automatic created', default=False)

    @api.multi
    def write(self, vals):
        vals['auto'] = vals.get('auto', False)
        return super(res_partner_agent, self).write(vals)
