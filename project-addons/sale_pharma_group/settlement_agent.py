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

from openerp import models, fields, api, _


class SettlementAgent(models.Model):

    _inherit = "settlement.agent"

    @api.multi
    def _get_agent_amounts(self):
        for sett in self:
            inv_amount = 0.0
            oth_amount = 0.0
            pha_amount = 0.0
            for line in sett.lines:
                if line.pharma_group_sale_id:
                    pha_amount += line.commission
                elif line.invoice_line_id:
                    inv_amount += line.commission
                else:
                    oth_amount += line.commission

            sett.invoice_amount = inv_amount
            sett.pharma_group_amount = pha_amount
            sett.other_amount = oth_amount

    invoice_amount = fields.Float(compute='_get_agent_amounts')
    pharma_group_amount = fields.Float(compute='_get_agent_amounts')
    other_amount = fields.Float(compute='_get_agent_amounts')
    lines = fields.One2many('settlement.line', 'settlement_agent_id',
                            'Lines', readonly=False)

    def calcula(self, cr, uid, ids, date_from, date_to):
        super(SettlementAgent, self).calcula(cr, uid, ids, date_from, date_to)
        total_per = 0
        total_sections = 0

        pharma_obj = self.pool['pharma.group.sale']
        sett_line = self.pool['settlement.line']
        sagent = self.browse(cr, uid, ids)
        sales = pharma_obj.search(cr, uid, [('date', '>=', date_from),
                                            ('date', '<=', date_to),
                                            ('agent_id', '=',
                                             sagent.agent_id.id),
                                            ('settled', '=', False)])
        for sale in pharma_obj.browse(cr, uid, sales):
            line = sett_line.create(cr, uid, {'pharma_group_sale_id': sale.id,
                                              'settlement_agent_id':
                                              sagent.id,
                                              'commission_id':
                                              sale.agent_id.commission.id})
            line = sett_line.browse(cr, uid, line)
            line.calcula()
            if line.commission_id.type == 'fijo':
                total_per += line.commission
            elif line.commission_id.type == 'tramos':
                total_sections += line.commission
            sale.write({'settled': True,
                        'settled_qty': line.commission})

        sagent.write({'total': sagent.total + total_sections + total_per,
                      'total_sections': sagent.total_sections + total_sections,
                      'total_per': sagent.total_per + total_per})

    def action_invoice_create(self, cr, uid, ids, journal_id,
                              product_id, mode, context=None):
        if mode != 'by_concept':
            return super(SettlementAgent, self).\
                action_invoice_create(journal_id, product_id, mode)
        else:
            inv_obj = self.pool['account.invoice']
            prod_obj = self.pool['product.product']
            inv_line_obj = self.pool['account.invoice.line']
            res = {}

            for settlement in self.browse(cr, uid, ids, context=context):
                if (not settlement.total_sections) and (not settlement.total):
                    continue

                partner = settlement.agent_id.partner_id
                if not partner:
                    continue

                payment_term_id = partner.property_supplier_payment_term.id
                account_id = partner.property_account_payable.id

                inv_vals = {'name': settlement.settlement_id.name,
                            'origin': settlement.settlement_id.name,
                            'type': 'in_invoice',
                            'account_id': account_id,
                            'partner_id': partner.id,
                            'payment_term': payment_term_id,
                            'fiscal_position': partner.
                            property_account_position.id}
                cur_id = settlement.get_currency_id()
                if cur_id:
                    inv_vals['currency_id'] = cur_id
                if journal_id:
                    inv_vals['journal_id'] = journal_id
                invoice_id = inv_obj.create(cr, uid, inv_vals)

                res[settlement.id] = invoice_id

                product = prod_obj.browse(cr, uid, product_id)
                account_id = product.product_tmpl_id.\
                    property_account_expense.id
                if not account_id:
                    account_id = product.categ_id.\
                        property_account_expense_categ.id
                # Cálculo de los impuestos a aplicar

                taxes = product.supplier_taxes_id

                # se añade la retención seleccionada de la ficha del agente
                if settlement.agent_id and settlement.agent_id.retention_id:
                    taxes.append(settlement.agent_id.retention_id)
                fpos_obj = settlement.agent_id.partner_id.\
                    property_account_position
                if settlement.agent_id and settlement.agent_id.partner_id:
                    tax_ids = fpos_obj.map_tax(taxes)
                    tax_ids = [x.id for x in tax_ids]
                else:
                    tax_ids = map(lambda x: x.id, taxes)

                account_id = fpos_obj.map_account(account_id)
                concept_amounts = []
                if settlement.invoice_amount:
                    concept_amounts.append((_('Settlements on invoices'),
                                           settlement.invoice_amount))
                if settlement.pharma_group_amount:
                    concept_amounts.\
                        append((_('Settlements on pharma groups sales'),
                               settlement.pharma_group_amount))

                if settlement.other_amount:
                    concept_amounts.append((_('Settlements on others'),
                                           settlement.other_amount))
                for amount in concept_amounts:
                    inv_line_obj.create(cr, uid,
                                        {'name': amount[0],
                                         'origin': amount[0],
                                         'invoice_id': invoice_id,
                                         'product_id': product.id,
                                         'account_id': account_id,
                                         'price_unit': amount[1],
                                         'quantity': 1,
                                         'invoice_line_tax_id': [(6, 0,
                                                                  tax_ids)]})

                inv_obj.button_compute(cr, uid, [invoice_id], set_total=True)
                settlement._invoice_hook(invoice_id)
            return res
