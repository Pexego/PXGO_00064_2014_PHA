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


class AssignZipAgentWizard(models.TransientModel):

    _name = 'assign.zip.agent.wizard'

    zip = fields.Char('Zip code')
    category_ids = fields.Many2many('res.partner.category',
                                    string='Categories', required=True)
    agent_id = fields.Many2one('sale.agent', 'Agent', compute="_get_agent")

    @api.multi
    def _get_agent(self):
        for wiz in self:
            wiz.agent_id = self.env.context.get('active_id', False)

    @api.multi
    def assign(self):
        self.ensure_one()
        zip_list = self.zip.replace(' ', '').split(',')
        all_location_ids = []
        for zip in zip_list:
            locations = self.env['res.better.zip'].search(
                [('name', '=', zip),
                 ('country_id', '=', self.agent_id.partner_id.country_id.id)])
            for location in locations:
                all_location_ids.append(location.id)
                for category in self.category_ids:
                    location_agents = location.agent_ids.filtered(
                        lambda record: record.category_id.id == category.id)
                    location_agents.unlink()
                    location_agents.create({'zip_id': location.id,
                                            'agent_id': self.agent_id.id,
                                            'category_id': category.id})
        update_partners = self.env['res.partner'].search(
            [('customer', '=', True), ('zip_id', 'in', all_location_ids)])
        update_partners.assign_agent()

    @api.multi
    def delete_all(self):
        self.ensure_one()
        for zip in self.agent_id.related_zip_ids:
            zip.unlink()
