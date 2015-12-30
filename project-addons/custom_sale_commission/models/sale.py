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


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def onchange_partner_id(self, part):
        res = super(SaleOrder, self).onchange_partner_id(part)
        agent_id = self.env['sale.agent'].search(
            ['|', ('user_id', '=', self.env.user.id),
             ('employee_id.user_id', '=', self.env.user.id)])
        if agent_id:
            if not res['value'].get('sale_agent_ids', False):
                res['value']['sale_agent_ids'] = []
            new_comm = (0, 0, {'agent_id': agent_id.id,
                               'commission_id': agent_id.commission.id})
            if new_comm not in res['value']['sale_agent_ids']:
                res['value']['sale_agent_ids'].append(new_comm)
        # related agents
        if agent_id or part:
            related = []
            if agent_id:
                related += agent_id.get_related_commissions()
            if part:
                partner = self.env['res.partner'].browse(part)
                for agent in partner.mapped('commission_ids.agent_id'):
                    related += agent.get_related_commissions()
            related_commissions = [(0, 0, x) for x in related]
            for commission in related_commissions:
                if commission not in res['value']['sale_agent_ids']:
                    res['value']['sale_agent_ids'].append(commission)
        return res


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def product_id_change_with_wh(self, pricelist, product,
                                  qty=0, uom=False, qty_uos=0, uos=False,
                                  name='', partner_id=False, lang=False,
                                  update_tax=True, date_order=False,
                                  packaging=False, fiscal_position=False,
                                  flag=False, warehouse_id=False):

        res = super(SaleOrderLine, self).product_id_change_with_wh(
            pricelist, product, qty, uom, qty_uos, uos, name,
            partner_id, lang, update_tax, date_order, packaging,
            fiscal_position, flag, warehouse_id)
        order_agent_obj = self.env['sale.order.agent']

        if product and not res['value']['line_agent_ids']:
            list_agent_ids = []
            product_obj = self.env['product.product'].browse(product)
            if not product_obj.commission_exent:
                order_agent_ids = []
                obj_list = []
                for agent in self._context.get('sale_agent_ids', []):
                    if type(agent[-1]) == type(obj_list):
                        obj_list += agent[-1]
                    else:
                        obj_list.append(agent[-1])
                for obj in obj_list:
                    if not obj:
                        continue
                    if type(obj) == type({}):
                        order_agent_ids.append(obj['agent_id'])
                    else:
                        order_agent_ids.append(order_agent_obj.browse(
                            obj).agent_id.id)
                dic = {}
                for category in product_obj.categ_ids:
                    for categ_commission in category.category_commission_ids:
                        # no hay agentes especificados para la comisión:
                        # se usan los agentes del pedido
                        if not categ_commission.agent_ids:
                            for agent_id in order_agent_ids:
                                if agent_id not in dic:
                                    dic[agent_id] = \
                                        categ_commission.commission_id.id
                        else:
                            for agent_id in categ_commission.agent_ids:
                                if agent_id.id in order_agent_ids:
                                    dic[agent_id.id] = \
                                        categ_commission.commission_id.id

                for k in dic:
                    line_agent_id = self._create_line_commission(k, dic[k])
                    list_agent_ids.append(int(line_agent_id))
                res['value']['line_agent_ids'] = list_agent_ids
        return res
