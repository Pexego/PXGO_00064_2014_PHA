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


class SaleReport(models.Model):
    _inherit = 'sale.report'

    cooperative_parent_id = fields.Many2one('res.partner', 'Parent cooperative')
    notified_partner_id = fields.Many2one('res.partner', 'Cooperative')
    sale_type = fields.Selection(selection=[('normal', 'Normal'),
                                            ('sample', 'Sample'),
                                            ('transfer', 'Transfer'),
                                            ('replacement', 'Replacement'),
                                            ('intermediary', 'Intermediary')],
                                 string='Type')
    sale_channel_id = fields.Many2one('sale.channel', 'Canal de venta')
    partner_creation_date = fields.Date('Partner creation date')
    partner_recovery_date = fields.Date('Partner recovery date')
    partner_parent_category = fields.Char('Partner parent category')
    partner_category = fields.Char('Partner category')
    commission_category = fields.Char('Commission category')
    categ_ids = fields.Many2many(related='product_id.categ_ids')
    third_parties = fields.Char('Third parties')
    country_id = fields.Many2one('res.country', 'Invoicing country')
    invoicing_state_id = fields.Many2one('res.country.state', 'Invoicing state')
    shipping_state_id = fields.Many2one('res.country.state', 'Shipping state')
    product_line = fields.Many2one('product.line', 'Product line')
    product_subline = fields.Many2one('product.subline', 'Product subline')
    product_container = fields.Many2one('product.container', 'Product container')
    product_form = fields.Many2one('product.form', 'Product form')
    product_clothing = fields.Selection((('dressed', 'Dressed'),
                                        ('naked', 'Naked')), 'Product clothing')
    product_year_appearance = fields.Char('Product year of appearance')
    product_cost = fields.Float('Product cost')
    product_cost_rm = fields.Float('Product cost raw material')
    product_cost_components = fields.Float('Product cost components')
    product_cost_dl = fields.Float('Product cost direct labor')
    product_gross_weight = fields.Float('Product gross weight')
    product_net_weight = fields.Float('Product net weight')
    is_delivery = fields.Boolean()  # Is a delivery carrier line?

    def _select(self):
        select_str = """,
            case
                when cp.parent_id is null then s.notified_partner_id
                else cp.parent_id
            end as cooperative_parent_id,
            s.notified_partner_id as notified_partner_id,
            s.sale_type as sale_type,
            s.sale_channel_id as sale_channel_id,
            pa.create_date as partner_creation_date,
            pa.recovery_date as partner_recovery_date,
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
                when t.customer is not null then 'Terceros'
                else 'Propios'
            end as third_parties,
            pa.country_id as country_id,
            ics.id as invoicing_state_id,
            scs.id as shipping_state_id,
            t.line as product_line,
            t.subline as product_subline,
            t.container_id as product_container,
            t.base_form_id as product_form,
            t.clothing as product_clothing,
            p.year_appearance as product_year_appearance,
            sum(l.product_uom_qty / u.factor * u2.factor * ip.value_float) as product_cost,
            sum(l.product_uom_qty * t.cost_price_rm) as product_cost_rm,
            sum(l.product_uom_qty * t.cost_price_components) as product_cost_components,
            sum(l.product_uom_qty * t.cost_price_dl) as product_cost_dl,
            sum(l.product_uom_qty * t.weight) as product_gross_weight,
            sum(l.product_uom_qty * t.weight_net) as product_net_weight,
            l.is_delivery
            """
        res = super(SaleReport, self)._select() + select_str
        res = res.replace(' min(l.id) as id,', ' l.id as id,')
        return res

    def _from(self):
        from_str = """
            left join res_partner cp on cp.id = s.notified_partner_id
            left join res_partner pa
                   on (pa.id = s.partner_id and pa.company_id = s.company_id)
            left join res_partner_category parent_rpc on parent_rpc.id = (
                    select
                        case
                            when rpc_aux.parent_id is null then parent_rpcr.category_id
                            else rpc_aux.parent_id
                        end
                    from res_partner_res_partner_category_rel parent_rpcr
                    join res_partner_category rpc_aux on rpc_aux.id = parent_rpcr.category_id
                    where parent_rpcr.partner_id = s.partner_id
                    limit 1
                )
            left join res_partner_category rpc on rpc.id = (
                    select rpcr.category_id
                    from res_partner_res_partner_category_rel rpcr
                    where rpcr.partner_id = s.partner_id
                    limit 1
                )
            left join product_category pc on pc.id = (
                    select pcr.categ_id
                    from product_categ_rel pcr
                    join product_category pc_aux on pc_aux.id = pcr.categ_id
            		join product_category cpc on cpc.id = pc_aux.parent_id
            		 and cpc.commissions_parent_category is True
                    where pcr.product_id = p.id
                    limit 1
                )
            left join res_country_state ics on ics.id = pa.state_id
            left join res_country_state scs on scs.id = spa.state_id
            left join ir_model_fields imf on imf.model = 'product.template' and imf.name = 'standard_price'
            left join ir_property ip on ip.fields_id = imf.id and ip.res_id = 'product.template,' || t.id::text
            """
        res = super(SaleReport, self)._from() + from_str
        return res

    def _group_by(self):
        group_by_str = """,
            cooperative_parent_id,
            s.notified_partner_id,
            s.sale_type,
            s.sale_channel_id,
            partner_creation_date,
            partner_recovery_date,
            partner_parent_category,
            partner_category,
            commission_category,
            t.customer,
            pa.country_id,
            ics.id, scs.id,
            t.line,
            t.subline,
            t.container_id,
            t.base_form_id,
            t.clothing,
            p.year_appearance,
            l.is_delivery
            """
        res = super(SaleReport, self)._group_by() + group_by_str
        res = res.replace(' l.product_id,', ' l.id, l.product_id,')
        return res
