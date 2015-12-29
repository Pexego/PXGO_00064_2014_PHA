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


class SaleAgentRelateds(models.Model):

    _name = 'sale.agent.relateds'

    original_agent_id = fields.Many2one('sale.agent', 'Orig Agent')
    related_agent_id = fields.Many2one('sale.agent', 'Related agent')
    commission_id = fields.Many2one('commission', 'Commission')


class SaleAgent(models.Model):

    _inherit = 'sale.agent'

    user_id = fields.Many2one('res.users', 'User')
    invoice_concept = fields.Char('Invoice concept', help='Concept to be \
established in settlement')
    base_qty = fields.Float('Base quantity')
    related_zip_ids = fields.One2many('location.agent.category.rel',
                                      'agent_id', 'Zips')
    related_agent_ids = fields.One2many('sale.agent.relateds',
                                        'original_agent_id', 'Related agents')

    @api.multi
    def get_user(self):
        self.ensure_one()
        if self.type == 'asesor':
            return self.user_id
        else:
            return self.employee_id.user_id

    @api.multi
    def get_related_commissions(self):
        self.ensure_one()
        related_commissions = []
        for related in self.related_agent_ids:
            related_commissions.append(
                {'agent_id': related.related_agent_id.id,
                 'commission_id': related.commission_id.id})
            related_commissions += related.related_agent_id.get_related_commissions()
        return related_commissions
