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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    partner_category = fields.Char('Partner category')
    product_categories = fields.Char('Product categories')
    has_commission = fields.Boolean('Has commission')

    def _select(self):
        select_str = ', partner_category, product_categories, has_commission'
        return super(AccountInvoiceReport, self)._select() + select_str

    def _sub_select(self):
        select_str = ', rpc.name as partner_category' + \
                     ', pc.name as product_categories' + \
                     ', cpc.commissions_parent_category as has_commission'
        return super(AccountInvoiceReport, self)._sub_select() + select_str

    def _from(self):
        from_str = ' left join res_partner_res_partner_category_rel rpcr' + \
                   '   on rpcr.partner_id = ai.partner_id' + \
                   ' left join res_partner_category rpc' + \
                   '   on rpc.id = rpcr.category_id' + \
                   ' left join product_categ_rel pcr' + \
                   '   on pcr.product_id = pr.id' + \
                   ' left join product_category pc' + \
                   '   on pc.id = pcr.categ_id' + \
                   ' left join product_category cpc' + \
                   '   on cpc.id = pc.parent_id'
        return super(AccountInvoiceReport, self)._from() + from_str

    def _group_by(self):
        group_by_str = ', rpc.name, pc.name, cpc.commissions_parent_category'
        return super(AccountInvoiceReport, self)._group_by() + group_by_str