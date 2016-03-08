# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
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

from openerp import models, api, exceptions, _


class AccountInvoiceConfirm(models.TransientModel):
    _inherit = 'account.invoice.confirm'

    @api.multi
    def invoice_confirm(self):
        invoice_ids = self.env.context.get('active_ids', [])
        invoices = self.env['account.invoice'].browse(invoice_ids)
        orphan_invoices = []
        for invoice in invoices:
            if invoice.payment_mode_id and \
               invoice.payment_mode_id.banking_mandate_needed and \
               not invoice.mandate_id:
                orphan_invoices.append(invoice)

        if len(orphan_invoices) > 0:
            invoice_list = '\n'.join([x.origin if x.origin \
                                               else x.partner_id.name \
                                      for x in orphan_invoices])
            raise exceptions.Warning(_('The following invoices do not have the'
                                       ' needed mandates assigned:\n%s' %
                                       invoice_list))

        return super(AccountInvoiceConfirm, self).invoice_confirm()