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
                                    string='Categories')
    from_agent_id = fields.Many2one('sale.agent', 'Agent')
    country_id = fields.Many2one('res.country', 'Country')
    agent_id = fields.Many2one('sale.agent', 'Agent', compute="_get_agent")

    @api.multi
    def _get_agent(self):
        for wiz in self:
            wiz.agent_id = self.env.context.get('active_id', False)

    @api.multi
    def assign(self):
        self.ensure_one()
        update_partner_vals = [('customer', '=', True)]
        categ_vals = []
        if self.category_ids:
            categories = self.category_ids
        else:
            categories = self.env['res.partner.category'].search(categ_vals)

        update_partner_vals.append(('category_id', 'in', categories.ids))
        if not self.zip:
            zip_list = []
        else:
            zip_list = self.zip.replace(' ', '').split(',')
        zip_vals = []
        if zip_list:
            zip_vals.append(('name', 'in', zip_list))
        if self.country_id:
            zip_vals.append(('country_id', '=', self.country_id.id))
        zips = self.env['res.better.zip'].search(zip_vals)

        update_partner_vals.append(('zip_id', 'in', zips.ids))

        agent_cat_rel_vals = [('category_id', 'in', categories.ids),
                              ('zip_id', 'in', zips.ids)]
        if self.from_agent_id:
            update_partner_vals.append(('user_id', '=', self.from_agent_id.id))
            agent_cat_rel_vals.append(('agent_id', '=', self.from_agent_id.id))

        agent_cat_rel = self.env['location.agent.category.rel'].search(agent_cat_rel_vals)
        if self.from_agent_id:
            agent_cat_rel.write({'agent_id': self.agent_id.id})
        else:
            agent_cat_rel.unlink()
            for zip in zips:
                for category in categories:
                    self.env['location.agent.category.rel'].create(
                        {'agent_id': self.agent_id.id,
                         'zip_id': zip.id,
                         'category_id': category.id})
        update_partners = self.env['res.partner'].search(update_partner_vals)
        update_partners.assign_agent()

    @api.multi
    def delete_all(self):
        self.ensure_one()
        for zip in self.agent_id.related_zip_ids:
            zip.unlink()
