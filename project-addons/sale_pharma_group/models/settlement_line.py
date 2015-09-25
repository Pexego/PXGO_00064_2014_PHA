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

from openerp import models, fields, api, exceptions, _


class SettlementLine(models.Model):

    _inherit = "settlement.line"

    amount = fields.Float('Amount', readonly=False, required=True, default=0.0)
    commission = fields.Float('Quantity', readonly=True)
    name = fields.Char('Description', size=128)
    pharma_group_sale_id = fields.Many2one('pharma.group.sale',
                                           'Pharma group sale')
    commission_id = fields.Many2one('commission', 'Commission', readonly=False)

    @api.model
    def create(self, vals):
        line = super(SettlementLine, self).create(vals)
        if (not vals.get('pharma_group_sale_id') and
                not vals.get('invoice_line_id')):
            line.calcula()
        return line

    @api.one
    def calcula(self):
        if self.invoice_line_id:
            return super(SettlementLine, self).calcula()
        elif self.pharma_group_sale_id:
            if (self.pharma_group_sale_id.agent_id.id ==
                    self.settlement_agent_id.agent_id.id):
                comm = self.pharma_group_sale_id.agent_id.commission
                self.amount = self.pharma_group_sale_id.price_unit * \
                    self.pharma_group_sale_id.product_qty
                self.commission_id = comm.id
                if comm.type == "fijo":
                    self.commission = self.amount * float(comm.fix_qty) / 100.0
                elif comm.type == "tramos":
                    self.commission = comm.calcula_tramos(self.amount)

        elif self.amount and self.commission_id:
            comm = self.commission_id
            if comm.type == "fijo":
                self.commission = self.amount * \
                    float(comm.fix_qty) / 100.0
            elif comm.type == "tramos":
                self.commission = comm.calcula_tramos(self.amount)
            sett = self.settlement_agent_id
            sett.total_per = sett.total_per + self.commission
            sett.total = sett.total + self.commission
