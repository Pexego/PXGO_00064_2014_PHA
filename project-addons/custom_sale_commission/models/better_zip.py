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


class LocationAgentCategoryRel(models.Model):

    _name = 'location.agent.category.rel'

    agent_id = fields.Many2one('sale.agent', 'Agent', required=True)
    zip_id = fields.Many2one('res.better.zip', 'Zip', required=True)
    category_id = fields.Many2one('res.partner.category', 'Category',
                                  required=True)


class BetterZip(models.Model):

    _inherit = "res.better.zip"

    agent_ids = fields.One2many('location.agent.category.rel', 'zip_id',
                                'Agents')
