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


class assign_zip_agent_wizard(models.TransientModel):

    _name = 'assign.zip.agent.wizard'

    zip = fields.Char('Zip code', size=64)
    agent_id = fields.Many2one('sale.agent', 'Agent', compute="_get_agent")

    def _get_agent(self):
        self.agent_id = self.env.context.get('active_id', False)

    @api.one
    def assign(self):
        locations = self.env['res.better.zip'].search([('name', '=', self.zip)])
        for location in locations:
            location.agent_id = self.agent_id
