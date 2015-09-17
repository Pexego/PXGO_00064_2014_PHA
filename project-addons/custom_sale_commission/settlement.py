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


class SettlementAgent(models.Model):

    _inherit = 'settlement.agent'

    invoice_concept = fields.Char('Invoice concept', help='Concept to be \
established in the invoice')

    @api.model
    def create(self, vals):
        if vals.get('agent_id', False):
            vals['invoice_concept'] = self.env['sale.agent'].browse(
                vals.get('agent_id')).invoice_concept
        return super(SettlementAgent,self).create(vals)

    @api.multi
    def _invoice_hook(self, invoice_id):
        invoice = self.env['account.invoice'].browse(invoice_id)
        invoice.name = self.invoice_concept
        return super(SettlementAgent, self)._invoice_hook(invoice_id)
