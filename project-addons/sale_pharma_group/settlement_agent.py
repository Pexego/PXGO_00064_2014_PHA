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
        set_agent = self.browse(cr, uid, ids)
        commission_obj = self.pool.get('commission.bussines.line')
        user = self.pool.get('res.users').browse(cr, uid, uid)
        # Recalculamos todas las lineas sujetas a comision

        sql = 'SELECT  invoice_line_agent.id FROM account_invoice_line ' \
              'INNER JOIN invoice_line_agent ON invoice_line_agent.invoice_line_id=account_invoice_line.id ' \
              'INNER JOIN account_invoice ON account_invoice_line.invoice_id = account_invoice.id ' \
              'WHERE invoice_line_agent.agent_id=' + str(set_agent.agent_id.id) + ' AND invoice_line_agent.settled=True ' \
              'AND account_invoice.state not in (\'draft\',\'cancel\') AND account_invoice.type=\'out_invoice\''\
              'AND account_invoice.date_invoice >= \'' + date_from + '\' AND account_invoice.date_invoice <= \'' + date_to + '\''\
              ' AND account_invoice.company_id = ' + str(user.company_id.id)

        cr.execute(sql)
        res = cr.fetchall()
        inv_line_agent_ids = [x[0] for x in res]

        self.pool.get('invoice.line.agent').calculate_commission(
            cr, uid, inv_line_agent_ids)

        sql = 'SELECT  account_invoice_line.id FROM account_invoice_line ' \
              'INNER JOIN invoice_line_agent ON invoice_line_agent.invoice_line_id=account_invoice_line.id ' \
              'INNER JOIN account_invoice ON account_invoice_line.invoice_id = account_invoice.id ' \
              'WHERE invoice_line_agent.agent_id=' + str(set_agent.agent_id.id) + ' AND invoice_line_agent.settled=False ' \
              'AND account_invoice.state not in (\'draft\',\'cancel\') AND account_invoice.type in (\'out_invoice\',\'out_refund\')'\
              'AND account_invoice.date_invoice >= \'' + date_from + '\' AND account_invoice.date_invoice <= \'' + date_to + '\''\
              ' AND account_invoice.company_id = ' + str(user.company_id.id)

        cr.execute(sql)
        res = cr.fetchall()
        inv_line_ids = [x[0] for x in res]

        total_per = 0
        total_sections = 0
        total = 0
        sections = {}
        for inv_line_id in inv_line_ids:
            linea_id = self.pool.get('settlement.line').create(
                cr, uid, {'invoice_line_id': inv_line_id,
                          'settlement_agent_id': ids})
            self.pool.get('settlement.line').calcula(cr, uid, linea_id)

            line = self.pool.get('settlement.line').browse(cr, uid, linea_id)

            analytic = line.invoice_line_id.account_analytic_id
            commission_applied = commission_obj.search(cr, uid, [('bussiness_line_id', '=', analytic.id), ('commission_id', '=', line.commission_id.id)])
            if not commission_applied:
                commission_applied = commission_obj.search(cr, uid, [('bussiness_line_id', '=', False), ('commission_id', '=', line.commission_id.id)])
            if not commission_applied:
                raise exceptions.except_orm(_('Commission Error'), _('not found the appropiate commission.'))
            commission = commission_obj.browse(cr, uid, commission_applied[0])

            # Marca la comision en la factura como liquidada y establece la
            # cantidad Si es por tramos la cantidad será cero, pero se
            # reflejará sobre el tramo del Agente

            if commission.type == "fijo":
                total_per = total_per + line.commission
                inv_ag_ids = self.pool.get('invoice.line.agent').search(
                    cr, uid, [('invoice_line_id', '=', inv_line_id),
                              ('agent_id', '=', set_agent.agent_id.id)])
                self.pool.get('invoice.line.agent').write(cr, uid, inv_ag_ids,
                                                          {'settled': True,
                                                           'quantity':
                                                               line.commission}
                                                          )
            if commission.type == "tramos":
                if line.invoice_line_id.product_id.commission_exent is not \
                        True:
                    # Hacemos un agregado de la base de cálculo agrupándolo
                    # por las distintas comisiones en tramos que tenga el
                    # agente asignadas
                    if line.invoice_line_id.invoice_id.type == 'out_refund':
                        sign_price = - line.invoice_line_id.price_subtotal
                    else:
                        sign_price = line.invoice_line_id.price_subtotal

                    if commission.id in sections:
                        sections[commission.id]['base'] = \
                            sections[commission.id]['base'] + \
                            sign_price
                        # Añade la línea de la que se añade esta
                        # base para el cálculo por tramos
                        sections[commission.id]['lines'].append(line)
                    else:
                        sections[commission.id] = \
                            {'type': commission,
                             'base': sign_price, 'lines': [line]}
        # Tramos para cada tipo de comisión creados
        for tramo in sections:
            # Cálculo de la comisión  para cada tramo
            #TODO
            new_tramo = {'commission': sections[tramo]['type'].calcula_tramos(
                sections[tramo]['base'])}
            sections[tramo].update(new_tramo)
            total_sections = total_sections+sections[tramo]['commission']
            # reparto de la comisión para cada linea

            for linea_tramo in sections[tramo]['lines']:
                com_por_linea = sections[tramo]['commission'] * \
                    (linea_tramo.invoice_line_id.price_subtotal /
                     (abs(sections[tramo]['base']) or 1.0))
                linea_tramo.write({'commission': com_por_linea})
                inv_ag_ids = self.pool.get('invoice.line.agent').search(
                    cr, uid,
                    [('invoice_line_id', '=', linea_tramo.invoice_line_id.id),
                     ('agent_id', '=', set_agent.agent_id.id)])
                self.pool.get('invoice.line.agent').write(cr, uid, inv_ag_ids,
                                                          {'settled': True,
                                                           'quantity':
                                                               com_por_linea})

        total = total_per + total_sections
        self.write(cr, uid, ids, {'total_per': total_per,
                                  'total_sections': total_sections,
                                  'total': total})


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
