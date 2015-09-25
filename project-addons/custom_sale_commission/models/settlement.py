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
    base_qty = fields.Float('Base quantity')

    @api.multi
    def write(self, vals):
        for line in self:
            total = vals.get('total', line.total)
            if total != 0:
                vals['total'] = total - line.base_qty + vals.get('base_qty', line.base_qty)
            else:
                vals['total'] = vals.get('base_qty', line.base_qty)
        return super(SettlementAgent, self).write(vals)

    @api.model
    def create(self, vals):
        if vals.get('agent_id', False):
            saleagent = self.env['sale.agent'].browse(vals.get('agent_id'))
            vals['invoice_concept'] = saleagent.invoice_concept
            vals['base_qty'] = saleagent.base_qty
            vals['total'] = vals.get('total', 0.0) + vals['base_qty']
        return super(SettlementAgent, self).create(vals)

    @api.multi
    def _invoice_hook(self, invoice_id):
        invoice = self.env['account.invoice'].browse(invoice_id)
        invoice.name = self.invoice_concept
        return super(SettlementAgent, self)._invoice_hook(invoice_id)

    @api.multi
    def action_invoice_create(self, journal_id, product_id, mode):
        res = super(SettlementAgent, self).action_invoice_create(
            journal_id, product_id, mode)
        for settlement in self:
            invoice_id = res[settlement.id]
            product = self.env['product.product'].browse(product_id)
            if settlement.base_qty:
                account_id = product.product_tmpl_id.\
                    property_account_expense.id
                if not account_id:
                    account_id = product.categ_id.\
                        property_account_expense_categ.id
                # Cálculo de los impuestos a aplicar

                taxes = product.supplier_taxes_id

                # se añade la retención seleccionada de la ficha del agente
                if settlement.agent_id and settlement.agent_id.retention_id:
                    taxes += settlement.agent_id.retention_id
                fpos_obj = settlement.agent_id.partner_id.\
                    property_account_position
                if settlement.agent_id and settlement.agent_id.partner_id:
                    tax_ids = fpos_obj.map_tax(taxes)
                    tax_ids = [x.id for x in tax_ids]
                else:
                    tax_ids = map(lambda x: x.id, taxes)

                account_id = fpos_obj.map_account(account_id)
                self.env['account.invoice.line'].create(
                    {'name': 'base',
                     'invoice_id': invoice_id,
                     'product_id': product_id,
                     'account_id': account_id,
                     'price_unit': settlement.base_qty,
                     'quantity': 1,
                     'invoice_line_tax_id': [(6, 0, tax_ids)]})
        return res
