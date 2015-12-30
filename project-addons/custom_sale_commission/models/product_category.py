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


class ProductCategory(models.Model):

    _inherit = 'product.category'
    category_commission_ids = fields.One2many('category.agent.commission',
                                              'category_id', 'Agents')


class CategoryAgentCommission(models.Model):

    _name = 'category.agent.commission'

    category_id = fields.Many2one('product.category', 'product.category')
    commission_id = fields.Many2one('commission', 'Applied commission',
                                    required=True)
    agent_ids = fields.Many2many('sale.agent',
                                 'category_agent_sale_agent_rel',
                                 'product_commission_id',
                                 'agent_id', 'Agents')
