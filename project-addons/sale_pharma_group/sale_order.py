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

from openerp import models, fields
import itertools


class sale_order_line(models.Model):

    _inherit = 'sale.order.line'


    def product_id_change2(self, cr, uid, ids, pricelist, product, qty=0,
                           uom=False, qty_uos=0, uos=False, name='',
                           partner_id=False, lang=False, update_tax=True,
                           date_order=False, packaging=False,
                           fiscal_position=False,
                           flag=False, sale_agent_ids=[], context=None):
        res = {'value': {}}
        if product:
            list_agent_ids = []
            product_obj = self.pool.get("product.product").browse(cr, uid,
                                                                  product)
            sale_line_agent = self.pool.get("sale.line.agent")
            if ids:
                sale_line_agent.unlink(cr, uid, sale_line_agent.search(
                    cr, uid, [('line_id', 'in', ids)]))
                res['value']['line_agent_ids'] = []
            if not product_obj.commission_exent:
                order_comm_ids = [x[-1] for x in sale_agent_ids if x[0] != 2]
                order_comm_ids = list(itertools.chain(*order_comm_ids))
                order_agent_ids = [x.agent_id.id for x in self.pool.get(
                    "sale.order.agent").browse(cr, uid, order_comm_ids)]
                dic = {}
                for prod_record in product_obj.product_agent_ids:
                    # no hay agentes especificados para la comisión:
                    # se usan los agentes del pedido
                    if not prod_record.agent_ids:
                        for agent_id in order_agent_ids:
                            if agent_id not in dic:
                                dic[agent_id] = prod_record.commission_id.id
                    else:
                        for agent_id in prod_record.agent_ids:
                            if agent_id.id in order_agent_ids:
                                dic[agent_id.id] = prod_record.commission_id.id

                for k in dic:
                    line_agent_id = self._create_line_commission(cr, uid,
                                                                 ids, k,
                                                                 dic[k])
                    list_agent_ids.append(int(line_agent_id))
                res['value']['line_agent_ids'] = list_agent_ids
        return res

    def product_id_change(
            self, cr, uid, ids, pricelist, product, qty=0, uom=False,
            qty_uos=0, uos=False, name='', partner_id=False, lang=False,
            update_tax=True, date_order=False, packaging=False,
            fiscal_position=False, flag=False, context=None):
        if not context:
            context = {}
        agent = context.get('agent_id', False)

        res = super(sale_order_line, self).product_id_change(
            cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, context)
        if agent:
            res2 = self.product_id_change2(
                cr, uid, ids, pricelist, product, qty, uom, qty_uos, uos, name,
                partner_id, lang, update_tax, date_order, packaging,
                fiscal_position, flag, agent, context)
            res['value'] = dict(res['value'].items() + res2['value'].items())
        return res
