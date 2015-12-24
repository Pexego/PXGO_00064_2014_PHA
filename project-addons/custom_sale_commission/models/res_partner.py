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
        if not self.zip_id or not self.zip_id.agent_id:
            return
        changed = False
        for commission in self.commission_ids:
            if changed and commission.auto:
                commission.unlink()
                continue
            if commission.auto is True:
                commission.agent_id = self.zip_id.agent_id.id
                commission.commission_id = self.zip_id.agent_id.commission
                changed = True
        if not changed:
            self.env['res.partner.agent'].create(
                {'agent_id': self.zip_id.agent_id.id,
                 'commission_id': self.zip_id.agent_id.commission.id,
                 'partner_id': self.id, 'auto': True})
        self.user_id = self.zip_id.agent_id.get_user()


class res_partner_agent(models.Model):

    _inherit = 'res.partner.agent'

    auto = fields.Boolean('Automatic created', default=False)

    @api.multi
    def write(self, vals):
        vals['auto'] = vals.get('auto', False)
        return super(res_partner_agent, self).write(vals)
