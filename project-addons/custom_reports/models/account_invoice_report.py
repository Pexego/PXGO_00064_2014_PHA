# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import fields, models, tools


class AccountInvoiceReport(models.Model):
    _inherit = 'account.invoice.report'

    partner_id = fields.Many2one('res.partner', 'Partner (invoice send address)')
    partner_creation_date = fields.Date('Partner creation date')
    partner_recovery_date = fields.Date('Partner recovery date')
    partner_commercial_discount = fields.Float('Commercial discount (%)', digits=(5, 2))
    partner_financial_discount = fields.Float('Financial discount (%)', digits=(5, 2))
    commercial_partner_id = fields.Many2one('res.partner', 'Partner (invoicing address)')
    commercial_name = fields.Char('Partner (commercial name)')
    partner_parent_category = fields.Char('Partner parent category')
    partner_category = fields.Char('Partner category')
    partner_user_id = fields.Many2one('res.users', 'Customer\'s sales agent')
    commission_category = fields.Char('Commission category')
    categ_ids = fields.Many2many(related='product_id.categ_ids')
    third_parties = fields.Char('Third parties')
    shipping_country_id = fields.Many2one('res.country', 'Shipping country')
    invoicing_state_id = fields.Many2one('res.country.state', 'Invoicing state')
    shipping_state_id = fields.Many2one('res.country.state', 'Shipping state')
    product_reference = fields.Char('Product reference')
    product_with_reference = fields.Char('Product with reference')
    product_description = fields.Text('Product description')
    product_line = fields.Many2one('product.line', 'Product line')
    product_subline = fields.Many2one('product.subline', 'Product subline')
    product_purchase_line = fields.Many2one('product.purchase.line',
                                            'Product purchase line')
    product_purchase_subline = fields.Many2one('product.purchase.subline',
                                               'Product purchase subline')
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
    product_ecoembes_weight = fields.Float('Product ecoembes weight')
    registration_date = fields.Date('Registration date')
    number = fields.Char('Invoice number')
    price_total_dollars = fields.Float('Total Without Tax in Dollars')
    gross_amount = fields.Float('Gross amount')

    def _select(self):
        # select_str = super(AccountInvoiceReport, self)._select() + """,
        select_str = """select
            sub.id,
            sub.date,
            sub.product_id,
            sub.product_template_id,
            sub.partner_id,
            sub.country_id,
            sub.payment_term,
            sub.period_id,
            sub.uom_name,
            sub.currency_id,
            sub.journal_id,
            sub.fiscal_position,
            sub.user_id,
            sub.company_id,
            sub.nbr,
            sub.type,
            sub.state,
            sub.categ_id,
            sub.date_due,
            sub.account_id,
            sub.account_line_id,
            sub.partner_bank_id,
            sub.product_qty,
            sub.currency_rate,
            sub.price_total / sub.currency_rate as price_total,
            sub.price_average / sub.currency_rate as price_average,
            sub.residual / sub.currency_rate as residual,
            sub.commercial_partner_id,
            sub.section_id,
            sub.partner_shipping_id,
            sub.sale_channel_id,
            sub.commercial_name,
            sub.partner_user_id,
            sub.partner_creation_date,
            sub.partner_recovery_date,
            sub.partner_commercial_discount,
            sub.partner_financial_discount,
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
            sub.state_id as invoicing_state_id,
            scs.id as shipping_state_id,
            sub.product_reference,
            sub.product_with_reference,
            sub.product_description,
            sub.product_line,
            sub.product_subline,
            sub.product_purchase_line,
            sub.product_purchase_subline,
            sub.product_container,
            sub.product_form,
            sub.product_clothing,
            sub.product_year_appearance,
            sub.product_cost * ip.value_float as product_cost,
            sub.product_cost_rm,
            sub.product_cost_components,
            sub.product_cost_dl,
            sub.product_gross_weight,
            sub.product_net_weight,
            sub.product_ecoembes_weight,
            sub.registration_date,
            sub.number,
            sub.price_subtotal * sub.currency_rate_dollars / sub.currency_rate as price_total_dollars,
            sub.gross_amount
        """
        return select_str

    def _sub_select(self):
        # select_str = super(AccountInvoiceReport, self)._sub_select() + """,
        select_str = """select
            min(ail.id) AS id,
            count(ail.*) AS nbr,
            ail.product_id,
            ail.account_id AS account_line_id,
            ai.date_invoice AS date,
            ai.partner_id,
            ai.payment_term,
            ai.period_id,
            ai.currency_id,
            case
              when ai.currency_id = rc.currency_id then 1
              else (
                select cr.rate
                from currency_rate cr
                where cr.currency_id = ai.currency_id
                  and cr.date_start <= coalesce(ai.date_invoice, now())
                  and (cr.date_end is null or cr.date_end > coalesce(ai.date_invoice, now()))
              )
            end as currency_rate,
            case
              when rc.currency_id = 1 then 1  -- EUR
              else (
                select cr.rate
                from currency_rate cr
                where cr.currency_id = 3  -- USD
                  and cr.date_start <= coalesce(ai.date_invoice, now())
                  and (cr.date_end is null or cr.date_end > coalesce(ai.date_invoice, now()))
              )
            end as currency_rate_dollars,            
            ai.journal_id,
            ai.fiscal_position,
            ai.user_id,
            ai.company_id,
            ai.type,
            ai.state,
            ai.date_due,
            ai.account_id,
            ai.partner_bank_id,
            pt.id as product_template_id,
            pt.categ_id,
            u2.name as uom_name,
            sum(case
                 when ai.type in ('out_refund', 'in_invoice')
                    then (- ail.quantity) / u.factor * u2.factor
                    else ail.quantity / u.factor * u2.factor
                end) as product_qty,
            sum(case
                 when ai.type in ('out_refund', 'in_invoice')
                    then - ail.price_subtotal
                    else ail.price_subtotal
                end) as price_total,
            case
                 when ai.type in ('out_refund', 'in_invoice')
                then sum(- ail.price_subtotal)
                else sum(ail.price_subtotal)
            end / case
                   when sum(ail.quantity / u.factor * u2.factor) <> 0::numeric
                       then case
                            when ai.type in ('out_refund', 'in_invoice')
                                then sum((- ail.quantity) / u.factor * u2.factor)
                                else sum(ail.quantity / u.factor * u2.factor)
                            end
                       else 1::numeric
                  end as price_average,
            case
              when ai.type in ('out_refund', 'in_invoice')
                then - ai.residual
                else ai.residual
            end / (select count(*) from account_invoice_line l where invoice_id = ai.id) * count(*) as residual,
            ai.commercial_partner_id as commercial_partner_id,
            ai.section_id as section_id,
            ai.partner_shipping_id as partner_shipping_id,
            ai.sale_channel_id as sale_channel_id,
            partner.country_id,
            partner.state_id,
            partner.comercial as commercial_name,
            partner.create_date as partner_creation_date,
            partner.recovery_date as partner_recovery_date,
            partner.commercial_discount::numeric(5,2) as partner_commercial_discount,
            partner.financial_discount::numeric(5,2) as partner_financial_discount,
            partner.user_id as partner_user_id,
            pt.default_code as product_reference,
            '[' || pt.default_code || '] ' || pt.name as product_with_reference,
            pt.description as product_description,
            pt.line as product_line,
            pt.subline as product_subline,
            pt.purchase_line as product_purchase_line,
            pt.purchase_subline as product_purchase_subline,
            pt.container_id as product_container,
            pt.base_form_id as product_form,
            pt.clothing as product_clothing,
            pr.year_appearance::text as product_year_appearance,
            sum(case
                    when ai.type in ('out_refund', 'in_invoice') then -1
                    else 1
                end * ail.quantity / u.factor * u2.factor
            ) as product_cost,
            sum(case
                    when ai.type in ('out_refund', 'in_invoice') then -1
                    else 1
                end * ail.quantity * pt.cost_price_rm
            ) as product_cost_rm,
            sum(case
                    when ai.type in ('out_refund', 'in_invoice') then -1
                    else 1
                end * ail.quantity * pt.cost_price_components
            ) as product_cost_components,
            sum(case
                    when ai.type in ('out_refund', 'in_invoice') then -1
                    else 1
                end * ail.quantity * pt.cost_price_dl
            ) as product_cost_dl,
            sum(case
                    when ai.type in ('out_refund', 'in_invoice') then -1
                    else 1
                end * ail.quantity * pt.weight
            ) as product_gross_weight,
            sum(case
                    when ai.type in ('out_refund', 'in_invoice') then -1
                    else 1
                end * ail.quantity * pt.weight_net
            ) as product_net_weight,
            sum(case
                    when ai.type in ('out_refund', 'in_invoice') then -1
                    else 1
                end * ail.quantity * pt.ecoembes_weight
            ) as product_ecoembes_weight,
            ai.registration_date,
            ai.number,
            sum(case
                when ai.type in ('out_refund', 'in_invoice') then - ail.price_subtotal
                else ail.price_subtotal
            end) as price_subtotal,
            sum(case
                when ai.type in ('out_refund', 'in_invoice') then - ail.gross_amount
                else ail.gross_amount
            end) as gross_amount
        """
        return select_str

    def _from(self):
        # from_str = super(AccountInvoiceReport, self)._from() + """
        from_str = """
            from account_invoice_line ail
            join account_invoice ai on ai.id = ail.invoice_id
            join res_partner partner on ai.commercial_partner_id = partner.id
            join res_company rc on rc.id = ai.company_id
            left join product_product pr on pr.id = ail.product_id
            left join product_template pt on pt.id = pr.product_tmpl_id
            left join product_uom u on u.id = ail.uos_id
            left join product_uom u2 on u2.id = pt.uom_id
        """
        return from_str

    def _group_by(self):
        # group_by_str = super(AccountInvoiceReport, self)._group_by() + """,
        group_by_str = """group by
            ail.product_id,
            ail.account_id,
            ai.id,
            ai.partner_id,
            ai.period_id,
            ai.currency_id,
            ai.journal_id,
            ai.account_id,
            ai.partner_bank_id,
            ai.user_id,
            ai.company_id,
            ai.commercial_partner_id,
            ai.section_id,
            ai.partner_shipping_id,
            ai.sale_channel_id,
            ai.date_invoice,
            ai.date_due,
            ai.registration_date,
            ai.payment_term,
            ai.fiscal_position,
            ai.type,
            ai.state,
            ai.residual,
            ai.amount_total,
            ai.number,
            partner.country_id,
            partner.state_id,
            commercial_name,
            partner_creation_date,
            partner_recovery_date,
            partner_commercial_discount,
            partner_financial_discount,
            partner_user_id,
            rc.currency_id,
            pr.year_appearance,
            pt.id,
            pt.categ_id,
            pt.customer,
            pt.default_code,
            '[' || pt.default_code || '] ' || pt.name,
            pt.description,
            pt.line,
            pt.subline,
            pt.purchase_line,
            pt.purchase_subline,
            pt.container_id,
            pt.base_form_id,
            pt.clothing,
            u2.name,
            u2.id
        """
        return group_by_str

    def init(self, cr):
        # self._table = account_invoice_report
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""CREATE or REPLACE VIEW %s as (
            WITH currency_rate (currency_id, rate, date_start, date_end) AS (
                SELECT r.currency_id, r.rate, r.name AS date_start,
                    (SELECT name FROM res_currency_rate r2
                     WHERE r2.name > r.name AND
                           r2.currency_id = r.currency_id
                     ORDER BY r2.name ASC
                     LIMIT 1) AS date_end
                FROM res_currency_rate r
            )
            %s
            FROM (
                %s %s %s
            ) AS sub
            left join res_partner spa on spa.id = sub.partner_shipping_id and spa.company_id = sub.company_id
            left join res_country_state scs on scs.id = spa.state_id
            left join res_partner_category parent_rpc on parent_rpc.id = (
              select
                case
                  when rpc.parent_id is null then parent_rpcr.category_id
                  else rpc.parent_id
                end
              from res_partner_res_partner_category_rel parent_rpcr
              join res_partner_category rpc on rpc.id = parent_rpcr.category_id
              join res_partner rp on rp.id = sub.partner_id
              where parent_rpcr.partner_id = (case when rp.parent_id is null then rp.id else rp.parent_id end)
              limit 1
            )
            left join res_partner_category rpc on rpc.id = (
              select rpcr.category_id
              from res_partner_res_partner_category_rel rpcr
              join res_partner rp on rp.id = sub.partner_id
              where rpcr.partner_id = (case when rp.parent_id is null then rp.id else rp.parent_id end)
              limit 1
            )
            left join product_category pc on pc.id = (
              select pcr.categ_id
              from product_categ_rel pcr
              join product_category pc_aux on pc_aux.id = pcr.categ_id
              join product_category cpc on cpc.id = pc_aux.parent_id and cpc.commissions_parent_category is true
              where pcr.product_id = sub.product_template_id
              limit 1
            )
            join product_template pt on pt.id = sub.product_template_id
            left join ir_model_fields imf on imf.model = 'product.template' and imf.name = 'standard_price'
            left join ir_property ip on ip.fields_id = imf.id and ip.res_id = 'product.template,' || sub.product_template_id::text            
        )""" % (self._table, self._select(), self._sub_select(), self._from(),
                self._group_by()))