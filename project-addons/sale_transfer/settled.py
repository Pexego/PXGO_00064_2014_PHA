# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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


class settlement(models.Model):

    _inherit = 'settlement'

    def action_cancel(self, cr, uid, ids, context=None):
        """Cancela la liquidación"""
        super(settlement, self).action_cancel(cr, uid, ids, context)
        for settle in self.browse(cr, uid, ids):
            for agent in settle.settlement_agent_id:
                sale_ids = [x.id for x in agent.sale_transfer_ids]
                self.pool.get('sale.order').write(cr, uid, sale_ids,
                                                  {'settled': False}, context)
        return True


class settlement_agent(models.Model):

    _inherit = 'settlement.agent'

    commission_transfer = fields.Float('Total transfer')
    sale_transfer_ids = fields.One2many('sale.order', 'settlement_agent_id',
                                        'Transfers')

    def calcula(self, cr, uid, ids, date_from, date_to):
        super(settlement_agent, self).calcula(cr, uid, ids, date_from, date_to)
        currency_obj = self.pool.get('res.currency')
        sale_obj = self.pool.get('sale.order')
        order_line_obj = self.pool.get('sale.order.line')
        commission_obj = self.pool.get('commission.bussines.line')
        amount_total = 0
        user = self.pool.get('res.users').browse(cr, uid, uid)
        for set_agent in self.browse(cr, uid, ids):
            sale_ids = sale_obj.search(cr, uid,
                                       [('transfer', '=', True),
                                        ('settled', '=', False),
                                        ('state', '=', 'done'),
                                        ('date_order', '>=', date_from),
                                        ('date_order', '<=', date_to)])
            for sale in sale_obj.browse(cr, uid, sale_ids):
                for line in sale.order_line:
                    amount = 0
                    commissions_ = order_line_obj.get_applied_commission(line)
                    commissions = [x for x in commissions_
                                   if x.agent_id.id == set_agent.agent_id.id]
                    for commission in commissions:
                        # selecciona el asignado al agente para el que está
                        # liquidando
                        analytic = line.order_id.project_id
                        commission_applied = commission_obj.search(
                            cr, uid, [('commission_id', '=',
                                       commission.commission_id.id)])
                        if not commission_applied:
                            commission_applied = commission_obj.search(
                                cr, uid, [('commission_id', '=',
                                           commission.commission_id.id)])
                        if not commission_applied:
                            raise exceptions.except_orm(
                                _('Commission Error'),
                                _('not found the appropiate commission.'))
                        commission_app = commission_obj.browse(cr, uid, commission_applied[0])

                        line_amount = line.price_subtotal
                        if commission_app.type == "fijo":
                            commission_per = commission_app.fix_qty
                            # Para tener en cuenta las rectificativas
                            amount = amount + \
                                line.price_subtotal * \
                                float(commission_per) / 100

                        elif commission_app.type == "tramos":
                            amount = amount + self.pool.get('commission.bussines.line').calcula_tramos(
                                cr, uid, [commission_app.id], line_amount)

                        cc_amount_subtotal = sale.currency_id.id != \
                            user.company_id.currency_id.id and \
                            currency_obj.compute(cr, uid,
                                                 sale.currency_id.id,
                                                 user.company_id.currency_id.id,
                                                 line_amount,
                                                 round=False) or line_amount
                        cc_commission_amount = sale.currency_id.id != \
                            user.company_id.currency_id.id and \
                            currency_obj.compute(cr, uid,
                                                 sale.currency_id.id,
                                                 user.company_id.currency_id.id,
                                                 amount, round=False) or amount
                        linea_id = self.pool.get('settlement.line').create(
                            cr, uid, {'settlement_agent_id': set_agent.id,
                                      'name': sale.name + u"/" + line.name,
                                      'amount': cc_amount_subtotal,
                                      'commission': cc_commission_amount,
                                      'commission_id': commission.commission_id.id,
                                      'currency_id': sale.currency_id.id,
                                      }, context={'transfer': True})

                        amount_total += cc_commission_amount

                sale.write({'settlement_agent_id': set_agent.id,
                            'settled': True})
            self.write(cr, uid, set_agent.id,
                       {'commission_transfer': amount_total,
                        'total': set_agent.total + amount_total})


class settlement_line(models.Model):

    _inherit = 'settlement.line'

    @api.one
    @api.model
    def calcula(self):
        if self.env.context.get('transfer', False):
            return
        else:
            return super(settlement_line, self).calcula()
