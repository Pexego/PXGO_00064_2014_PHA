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
    @api.model
    def calcula(self):
        if self.invoice_line_id:
            currency_obj = self.env['res.currency']
            commission_obj = self.env['commission.bussines.line']
            amount = 0
            user = self.env.user
            # Recorre los agentes y condiciones asignados a la factura
            for commission in self.invoice_line_id.commission_ids:
                # selecciona el asignado al agente para el que está liquidando
                if commission.agent_id.id == self.settlement_agent_id.agent_id.id:
                    analytic = self.invoice_line_id.account_analytic_id
                    commission_applied = commission_obj.search([('bussiness_line_id', '=', analytic.id), ('commission_id', '=', commission.commission_id.id)])
                    if not commission_applied:
                        commission_applied = commission_obj.search([('bussiness_line_id', '=', False), ('commission_id', '=', commission.commission_id.id)])
                    if not commission_applied:
                        raise orm.except_orm(_('Commission Error'), _('not found the appropiate commission.'))
                    commission_app = commission_applied[0]
                    # commission_app = commission.commission_id  # Obtiene el objeto
                    invoice_line_amount = self.invoice_line_id.price_subtotal
                    if commission_app.type == "fijo":
                        commission_per = commission_app.fix_qty
                        # Para tener en cuenta las rectificativas
                        if self.invoice_line_id.invoice_id.type == 'out_refund':
                            amount = amount - \
                                self.invoice_line_id.price_subtotal * \
                                float(commission_per) / 100
                        else:
                            amount = amount + \
                                self.invoice_line_id.price_subtotal * \
                                float(commission_per) / 100

                    elif commission_app.type == "tramos":
                        invoice_line_amount = 0
                        amount = 0

                    cc_amount_subtotal = self.invoice_id.currency_id.id != \
                        user.company_id.currency_id.id and \
                        currency_obj.compute(cr, uid,
                                             self.invoice_id.currency_id.id,
                                             user.company_id.currency_id.id,
                                             invoice_line_amount,
                                             round=False) or invoice_line_amount
                    cc_commission_amount = self.invoice_id.currency_id.id != \
                        user.company_id.currency_id.id and \
                        currency_obj.compute(cr, uid,
                                             self.invoice_id.currency_id.id,
                                             user.company_id.currency_id.id,
                                             amount, round=False) or amount

                    self.write({'amount': cc_amount_subtotal,
                                'commission_id': commission.commission_id.id,
                                'commission': cc_commission_amount,
                                'currency_id': user.company_id.currency_id.id})

        elif self.pharma_group_sale_id:
            if (self.pharma_group_sale_id.agent_id.id ==
                    self.settlement_agent_id.agent_id.id):
                comm = self.pharma_group_sale_id.agent_id.commission_group
                self.amount = self.pharma_group_sale_id.price_unit * \
                    self.pharma_group_sale_id.product_qty
                self.commission = self.amount * float(comm) / 100.0

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
