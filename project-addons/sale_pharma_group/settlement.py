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

from openerp import models, fields, api


class Settlement(models.Model):

    _inherit = "settlement"

    settlement_agent_id = fields.One2many('settlement.agent',
                                         'settlement_id',
                                         'Settlement agents',
                                         readonly=False)

    @api.multi
    @api.model
    def action_cancel(self):
        res = super(Settlement, self).action_cancel()
        for settle in self:
            for settle_line in settle.settlement_agent_id:
                for line in settle_line.lines:
                    if line.pharma_group_sale_id:
                        line.pharma_group_sale_id.write({'settled': False,
                                                         'settled_qty': 0.0})

        return res
