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
    commission_category = fields.Char('Commission category')
    shipping_country_id = fields.Many2one('res.country', 'Shipping country')

    def _select(self):
        select_str = ', partner_category, commission_category, shipping_country_id'
        return super(AccountInvoiceReport, self)._select() + select_str

    def _sub_select(self):
        select_str = """
            , (
                select
                    rpc.name
                from res_partner_res_partner_category_rel rpcr,
                     res_partner_category rpc
                where rpcr.partner_id = ai.partner_id
                  and rpc.id = rpcr.category_id
                limit 1
            ) partner_category
            , (
                select
                    pc.name
                from product_categ_rel pcr, product_category pc, product_category cpc
                where pcr.product_id = pr.id
                  and pc.id = pcr.categ_id
                  and cpc.id = pc.parent_id and cpc.commissions_parent_category = true
                limit 1
            ) commission_category
            , spa.country_id as shipping_country_id
            """
        return super(AccountInvoiceReport, self)._sub_select() + select_str

    def _from(self):
        from_str = """
            left join res_partner spa on spa.id = ai.partner_shipping_id
                and spa.company_id = ai.company_id
            """
        return super(AccountInvoiceReport, self)._from() + from_str

    def _group_by(self):
        group_by_str = ', partner_category, commission_category, spa.country_id'
        return super(AccountInvoiceReport, self)._group_by() + group_by_str