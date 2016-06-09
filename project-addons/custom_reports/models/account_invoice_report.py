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

    partner_id = fields.Many2one('res.partner', 'Partner (invoice send address)')
    commercial_partner_id = fields.Many2one('res.partner', 'Partner (invoicing address)')
    commercial_name = fields.Char('Partner (commercial name)')
    partner_parent_category = fields.Char('Partner parent category')
    partner_category = fields.Char('Partner category')
    commission_category = fields.Char('Commission category')
    third_parties = fields.Char('Third parties')
    shipping_country_id = fields.Many2one('res.country', 'Shipping country')
    invoicing_state_id = fields.Many2one('res.country.state', 'Invoicing state')
    shipping_state_id = fields.Many2one('res.country.state', 'Shipping state')
    product_line = fields.Many2one('product.line', 'Product line')
    product_subline = fields.Many2one('product.subline', 'Product subline')
    product_container = fields.Many2one('product.container', 'Product container')
    product_form = fields.Many2one('product.form', 'Product form')
    product_clothing = fields.Selection((('dressed', 'Dressed'),
                                        ('naked', 'Naked')), 'Product clothing')
    product_cost = fields.Float('Product cost')

    def _select(self):
        select_str = """,
            commercial_name,
            partner_parent_category,
            partner_category,
            commission_category,
            third_parties,
            shipping_country_id,
            invoicing_state_id,
            shipping_state_id,
            product_line,
            product_subline,
            product_container,
            product_form,
            product_clothing,
            product_cost
            """
        return super(AccountInvoiceReport, self)._select() + select_str

    def _sub_select(self):
        select_str = """,
            partner.comercial as commercial_name,
            case
                when parent_rpc.name is null then '(Sin categoría)'
                else parent_rpc.name
            end as partner_parent_category,
            case
                when rpc.name is null then '(Sin categoría)'
                else rpc.name
            end as partner_category,
            case
                when pc.name is null then '(Sin categoría)'
                else pc.name
            end as commission_category,
            case
                when pt.customer is not null then 'Terceros'
                else 'Propios'
            end as third_parties,
            spa.country_id as shipping_country_id,
            ics.id as invoicing_state_id,
            scs.id as shipping_state_id,
            pt.line as product_line,
            pt.subline as product_subline,
            pt.container_id as product_container,
            pt.base_form_id as product_form,
            pt.clothing as product_clothing,
            sum(case
                    when ai.type in ('out_refund', 'in_invoice') then -1
                    else 1
                end * ail.quantity / u.factor * u2.factor * ip.value_float
            ) as product_cost
            """
        return super(AccountInvoiceReport, self)._sub_select() + select_str

    def _from(self):
        from_str = """
            left join res_partner_category parent_rpc on parent_rpc.id = (
                    select
                        case
                            when rpc_aux.parent_id is null then parent_rpcr.category_id
                            else rpc_aux.parent_id
                        end
                    from res_partner_res_partner_category_rel parent_rpcr
                    join res_partner_category rpc_aux on rpc_aux.id = parent_rpcr.category_id
                    where parent_rpcr.partner_id = partner.id
                    limit 1
                )
            left join res_partner_category rpc on rpc.id = (
                    select rpcr.category_id
                    from res_partner_res_partner_category_rel rpcr
                    where rpcr.partner_id = partner.id
                    limit 1
                )
            left join product_category pc on pc.id = (
                    select pcr.categ_id
                    from product_categ_rel pcr
                    join product_category pc_aux on pc_aux.id = pcr.categ_id
            		join product_category cpc on cpc.id = pc_aux.parent_id
            		 and cpc.commissions_parent_category is True
                    where pcr.product_id = pr.id
                    limit 1
                )
            left join res_partner spa on spa.id = ai.partner_shipping_id
                and spa.company_id = ai.company_id
            left join res_country_state ics on ics.id = partner.state_id
            left join res_country_state scs on scs.id = spa.state_id
            left join ir_model_fields imf on imf.model = 'product.template' and imf.name = 'standard_price'
            left join ir_property ip on ip.fields_id = imf.id and ip.res_id = 'product.template,' || pt.id::text
            """
        return super(AccountInvoiceReport, self)._from() + from_str

    def _group_by(self):
        group_by_str = """,
            commercial_name,
            partner_parent_category,
            partner_category,
            commission_category,
            pt.customer,
            spa.country_id,
            ics.id,
            scs.id,
            pt.line,
            pt.subline,
            pt.container_id,
            pt.base_form_id,
            pt.clothing
            """
        return super(AccountInvoiceReport, self)._group_by() + group_by_str
