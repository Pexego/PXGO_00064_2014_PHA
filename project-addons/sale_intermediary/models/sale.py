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


from openerp.osv import fields, osv


class my_sale_order(osv.Model):

    _inherit = 'sale.order'

    _columns = {
        'intermediary': fields.boolean('Intermediary'),
    }

    def _prepare_invoice(self, cr, uid, order, lines, context=None):
        """Prepare the dict of values to create the new invoice for a
           sale order. This method may be overridden to implement custom
           invoice generation (making sure to call super() to establish
           a clean extension chain).

           :param browse_record order: sale.order record to invoice
           :param list(int) line: list of invoice line IDs that must be
                                  attached to the invoice
           :return: dict of value to create() the invoice
        """
        invoice_vals = super(my_sale_order, self)._prepare_invoice(cr, uid, order,
                                                                lines, context)

        invoice_vals.update({
            'partner_shipping_id': order.partner_shipping_id.id,
        })

        # Care for deprecated _inv_get() hook - FIXME: to be removed after 6.1
        invoice_vals.update(self._inv_get(cr, uid, order, context=context))

        return invoice_vals

my_sale_order()


class my_account_invoice(osv.Model):

    _inherit = 'account.invoice'

    _columns = {
        'partner_shipping_id': fields.many2one('res.partner', 'Shipping to', required=False),
    }

my_account_invoice()


class my_account_invoice_report(osv.Model):

    _inherit = 'account.invoice.report'

    _columns = {
        'partner_shipping_id': fields.many2one('res.partner', 'Shipping to'),
    }

    def _select(self):
        return  super(my_account_invoice_report, self)._select() + ", sub.partner_shipping_id as partner_shipping_id"

    def _sub_select(self):
        return  super(my_account_invoice_report, self)._sub_select() + ", ai.partner_shipping_id as partner_shipping_id"

    def _group_by(self):
        return super(my_account_invoice_report, self)._group_by() + ", ai.partner_shipping_id"

my_account_invoice_report()