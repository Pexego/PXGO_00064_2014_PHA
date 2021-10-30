# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from lxml import etree
from openerp.exceptions import Warning
import math


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    budget = fields.Boolean(default=False)
    delivery_date = fields.Date()
    location_dest_id = fields.Many2one(string='Destination Location',
                                       comodel_name='stock.location')

    @api.multi
    def action_button_confirm(self):
        warning_messages = ''
        for sale_id in self:
            if sale_id.budget:
                raise Warning(_('An order budget can not be confirmed!'))

            if not sale_id.partner_id.vat and \
                    not (sale_id.partner_id.simplified_invoice and
                         sale_id.partner_id.sii_simplified_invoice):
                warning_messages += '[{}] {}\n'.format(sale_id.name,
                                                       sale_id.partner_id.name)
        if warning_messages:
            raise Warning(_('Cannot continue due to sale orders with '
                            'customers without VAT number and '
                            'without simplified invoice marking:\n'),
                            warning_messages)

        return super(SaleOrder, self).action_button_confirm()

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False,
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

    @api.model
    def action_ship_create(self):
        res = super(SaleOrder, self).action_ship_create()
        if self.delivery_date:
            for move_id in self.picking_ids.mapped(lambda p: p.move_lines):
                move_id.date_expected = self.delivery_date
        return res

    @api.model
    def create(self, vals):
        if self.env.user in self.env.\
                ref('custom_permissions.group_salesman_ph').users:
            vals['budget'] = True
        return super(SaleOrder, self).create(vals)
