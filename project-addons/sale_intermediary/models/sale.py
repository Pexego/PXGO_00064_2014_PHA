# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus I+D+i All Rights Reserved
#    $Iván Alvarez <informatica@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


from openerp import fields, models
from openerp.osv import osv


class my_sale_order(models.Model):

    _inherit = 'sale.order'
    intermediary = fields.Boolean("Sale by intermediary", default=False)


class my_account_invoice(models.Model):
    _inherit = 'account.invoice'
    partner_shipping_id = fields.Many2one('res.partner' , 'Shipping to', required=False )


class my_stock_picking(osv.osv):

    _inherit = "stock.picking"

    def _get_invoice_vals(self, cr, uid, key, inv_type, journal_id, move, context=None):
        inv_vals = super(my_stock_picking, self)._get_invoice_vals(cr, uid, key, inv_type, journal_id, move, context=context)
        sale = move.picking_id.sale_id
        if sale:
            inv_vals.update({
                'partner_shipping_id': sale.partner_shipping_id.id,
            })
        return inv_vals


class my_account_invoice_report(models.Model):
    _inherit = 'account.invoice.report'
    partner_shipping_id = fields.Many2one('res.partner', 'Shipping to')

    def _select(self):
        return  super(my_account_invoice_report, self)._select() + ", sub.partner_shipping_id as partner_shipping_id"

    def _sub_select(self):
        return  super(my_account_invoice_report, self)._sub_select() + ", ai.partner_shipping_id as partner_shipping_id"

    def _group_by(self):
        return super(my_account_invoice_report, self)._group_by() + ", ai.partner_shipping_id"
