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
from openerp.osv import fields,osv

class account_invoice_report(osv.osv):

    _inherit = 'account.invoice.report'
    _columns = {
        'section_id': fields.many2one('crm.case.section', 'Sales Team'),
    }
    _depends = {
        'account.invoice': ['section_id'],
    }

    def _select(self):
        return  super(account_invoice_report, self)._select() + ", sub.section_id as section_id"

    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", ai.section_id as section_id"

    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + ", ai.section_id"

account_invoice_report()


class my_account_invoice_report(osv.osv):

    _inherit = 'account.invoice.report'
    _columns = {
        'sale_channel_id': fields.many2one('sale_channel', 'Canal de venta'),
    }
    _depends = {
        'account.invoice': ['sale_channel_id'],
    }

    def _select(self):
        return  super(account_invoice_report, self)._select() + ", sub.sale_channel_id as sale_channel_id"

    def _sub_select(self):
        return  super(account_invoice_report, self)._sub_select() + ", ai.sale_channel_id as sale_channel_id"

    def _group_by(self):
        return super(account_invoice_report, self)._group_by() + ", ai.sale_channel_id"

my_account_invoice_report()