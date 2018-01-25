# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
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
from lxml import etree
from openerp.exceptions import Warning
import math


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    budget = fields.Boolean(default=False)

    @api.multi
    def action_button_confirm(self):
        for sale in self:
            if sale.budget:
                raise Warning(_('An order budget can not be confirmed!'))
        return super(SaleOrder, self).action_button_confirm()

    @api.model
    def fields_view_get(self, view_id=None, view_type=False, toolbar=False,
                        submenu=False):
        # If current user is a member of SalesmanPH, show only his/her clients,
        # otherwise, show all clients
        res = super(SaleOrder, self).fields_view_get(view_id=view_id,
                                                     view_type=view_type,
                                                     toolbar=toolbar,
                                                     submenu=submenu)
        if view_type == 'form' and res['model'] == 'sale.order':
            doc = etree.XML(res['arch'])
            if self.env.user not in \
                    self.env.ref('custom_permissions.group_salesman_ph').users:
                for node in doc.xpath("/form/sheet/group/group/field[@name='partner_id']"):
                    domain = node.get('domain')
                    domain = domain.replace(",('user_id','=',uid)", "")
                    node.set('domain', domain)
            res['arch'] = etree.tostring(doc)
        return res

    @api.multi
    def onchange_partner_id(self, partner):
        res = super(SaleOrder, self).onchange_partner_id(partner)
        intermediary = self.env.context.get('intermediary', False)

        # Dynamic filters for invoice and shipping combos
        if partner and intermediary:
            res['domain'] = {
                'partner_invoice_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False),
                    '|', ('parent_id', '=', partner), ('id', '=', partner)
                ],
                'partner_shipping_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False)
                ]
            }
        elif partner and not intermediary:
            res['domain'] = {
                'partner_invoice_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False),
                    '|', ('parent_id', '=', partner), ('id', '=', partner)
                ],
                'partner_shipping_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False),
                    '|', ('parent_id', '=', partner), ('id', '=', partner)
                ]
            }
        else:
            res['domain'] = {
                'partner_invoice_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False)
                ],
                'partner_shipping_id': [
                    ('customer', '=', True),
                    ('pre_customer', '=', False)
                ]
            }

        # Recover default partner picking policy
        if partner:
            partner_id = self.env['res.partner'].browse(partner)
            if partner_id.picking_policy:
                res['value']['picking_policy'] = partner_id.picking_policy

        return res

    @api.multi
    def duplicate(self):
        res = self.copy()

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': res.id,
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
            'nodestroy': True,
            'context': self.env.context
        }

    @api.multi
    def delivery_set_vat(self):
        res = self.delivery_set()
        for order in self:
            carrier_order_line = order.order_line.filtered(lambda r: r.id in res)
            order_lines = order.order_line - carrier_order_line
            carrier_tax_ids = carrier_order_line.tax_id
            carrier_tax_amount = math.fsum(tax.amount for tax in carrier_tax_ids)
            max_tax_amount = 0
            for ol in order_lines:
                if ol.gross_amount and \
                   math.fsum(tax.amount for tax in ol.tax_id) > max_tax_amount:
                    highest_tax_ids = ol.tax_id
                    max_tax_amount = math.fsum(tax.amount for tax in ol.tax_id)
            if carrier_tax_amount != max_tax_amount:
                carrier_order_line.tax_id = highest_tax_ids
