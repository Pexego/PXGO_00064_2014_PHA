# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
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
from openerp import models, fields


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'
    sale_channel_id = fields.Many2one('sale.channel', 'Canal de venta')

    def _select(self):
        return  super(AccountInvoiceReport, self)._select() + \
                ", sub.sale_channel_id as sale_channel_id"

    def _sub_select(self):
        return  super(AccountInvoiceReport, self)._sub_select() + \
                ", ai.sale_channel_id as sale_channel_id"

    def _group_by(self):
        return super(AccountInvoiceReport, self)._group_by() +\
               ", ai.sale_channel_id"
