# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
from datetime import datetime
import time


class PurchasableProducts(models.TransientModel):
    _name = 'purchasable.products'
    _inherits = {'product.product': 'product_id'}
    _rec_name = 'product_id'

    request_id = fields.Integer()
    partner_id = fields.Many2one(comodel_name='res.partner')
    partner_ref = fields.Char(related='partner_id.ref', readonly=True)
    product_id = fields.Many2one(string='Product',
                                 comodel_name='product.product', required=True,
                                 ondelete='cascade', readonly=True)
    supplier_ref = fields.Char(string='Supplier reference', readonly=True)
    qty_current_year = fields.Float(digits=(16,2), string='Current year qty.')
    price_current_year = fields.Float(digits=(16,2), string='Current year amount')
    qty_last_year = fields.Float(digits=(16,2), string='Last year qty.')
    price_last_year = fields.Float(digits=(16,2), string='Last year amount')
    qty_year_before = fields.Float(digits=(16,2), string='Year before qty.')
    price_year_before = fields.Float(digits=(16,2), string='Year before amount')
    qty_other_years = fields.Float(digits=(16,2), string='Other years qty.')
    price_other_years = fields.Float(digits=(16,2), string='Other years amount')
    price_list_member = fields.Boolean(string='Price list member?')
    price_list_ids = fields.One2many(comodel_name='pricelist.partnerinfo',
                                     compute='_get_price_lists',
                                     readonly=True)
    invoice_line_ids = fields.One2many(comodel_name='account.invoice.line',
                                       compute='_get_invoices_lines',
                                       readonly=True)

    @api.one
    def _get_price_lists(self):
        self.price_list_ids = self.env['pricelist.partnerinfo'].search([
            ('suppinfo_id.product_tmpl_id', '=', self.product_id.product_tmpl_id.id)
        ])

    @api.one
    def _get_invoices_lines(self):
        self.invoice_line_ids = self.env['account.invoice.line'].search([
            ('product_id', '=', self.product_id.id),
            ('invoice_id.type', 'in', ('in_invoice', 'in_refund')),
            ('invoice_id.state', '!=', 'cancel'),
            ('invoice_id.date_invoice', '!=', False)
        ])

    @api.model
    def _get_products(self, partner_id):
        if not partner_id.supplier:
            return False

        inv_lines = self.env['account.invoice.line'].search([
            ('invoice_id.commercial_partner_id', '=', partner_id.id),
            ('invoice_id.type', 'in', ('in_invoice', 'in_refund')),
            ('invoice_id.state', '!=', 'cancel'),
            ('invoice_id.date_invoice', '!=', False)
        ])

        price_lists = self.env['product.supplierinfo'].search([
            ('name', '=', partner_id.id)
        ])

        if not inv_lines:
            return False

        # Unique id for domain filtering
        request_id = int(round(time.time()))

        products = {}
        product_data = {
                    'request_id': request_id,
                    'partner_id': False,
                    'product_id': False,
                    'supplier_ref': '',
                    'qty_current_year': 0,
                    'price_current_year': 0,
                    'qty_last_year': 0,
                    'price_last_year': 0,
                    'qty_year_before': 0,
                    'price_year_before': 0,
                    'qty_other_years': 0,
                    'price_other_years': 0,
                    'price_list_member': False
                }

        current_year = datetime.now().year
        for ail in inv_lines:
            year_idx = current_year - \
                       fields.Date.from_string(ail.invoice_id.date_invoice).year
            prod_idx = ail.product_id.id
            if prod_idx not in products:
                products[prod_idx] = dict(product_data)
                products[prod_idx]['partner_id'] = partner_id.id
                products[prod_idx]['product_id'] = ail.product_id.id
                pl = price_lists.filtered(lambda r:
                                          r.product_tmpl_id ==
                                          ail.product_id.product_tmpl_id)
                products[prod_idx]['supplier_ref'] = pl.product_code if pl else ''

            sign = -1 if ail.invoice_id.type == 'in_refund' else 1

            if year_idx == 0:
                products[prod_idx]['qty_current_year'] += ail.quantity * sign
                products[prod_idx]['price_current_year'] += ail.price_subtotal * sign
            elif year_idx == 1:
                products[prod_idx]['qty_last_year'] += ail.quantity * sign
                products[prod_idx]['price_last_year'] += ail.price_subtotal * sign
            elif year_idx == 2:
                products[prod_idx]['qty_year_before'] += ail.quantity * sign
                products[prod_idx]['price_year_before'] += ail.price_subtotal * sign
            else:
                products[prod_idx]['qty_other_years'] += ail.quantity * sign
                products[prod_idx]['price_other_years'] += ail.price_subtotal * sign

        for pl in price_lists:
            if pl.product_tmpl_id.product_variant_count > 0:
                prod_idx = pl.product_tmpl_id.product_variant_ids[0].id
                if prod_idx not in products:
                    products[prod_idx] = dict(product_data)
                    products[prod_idx]['partner_id'] = partner_id.id
                    products[prod_idx]['product_id'] = prod_idx
                    products[prod_idx]['supplier_ref'] = pl.product_code
                products[prod_idx]['price_list_member'] = True

        for prod_idx in products:
            self.create(products[prod_idx])

        return request_id

    @api.multi
    def view_product_price_lists_and_invoices(self):
        view_id = self.env.ref('custom_views.purchasable_products_form_view').id

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id,
            'res_model': 'purchasable.products',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.model
    def search(self, args, offset=0, limit=None, order=None, count=False):
        if self.env.context.get('show_all_suppliers', False):
            # Unique id for domain filtering
            request_id = int(round(time.time()))

            self.env.cr.execute("""
                insert into purchasable_products (request_id, partner_id, supplier_ref,
                    product_id, create_uid, create_date, write_uid, write_date)
                select distinct
                    {1:d} as request_id,
                    suppliers.partner_id,
                    rp.ref,
                    suppliers.product_id,
                    {0:d} as create_uid,
                    current_date as create_date,
                    {0:d} as write_uid,
                    current_date as write_date                 
                from (
                    select distinct
                        ai.commercial_partner_id "partner_id",
                        ail.product_id "product_id"
                    from account_invoice ai
                    join account_invoice_line ail on ail.invoice_id = ai.id
                    join product_product pp on pp.id = ail.product_id and pp.active
                    where ai.company_id = 1
                      and ai.date_invoice is not null
                      and ai.state != 'cancel'
                      and ai.type in ('in_invoice', 'in_refund')
                
                    union
                
                    select distinct
                        ps.name "partner_id",
                        pp.id "product_id"
                    from product_supplierinfo ps
                    join product_product pp on pp.product_tmpl_id = ps.product_tmpl_id and pp.active
                    where ps.company_id = 1
                      and ps.active_supplier
                ) as suppliers
                join res_partner rp on rp.id = suppliers.partner_id and rp.active
            """.format(self.env.user.id, request_id))
            args.append(('request_id', '=', request_id))

        return super(PurchasableProducts, self).search(args, offset=offset,
                                                       limit=limit, order=order,
                                                       count=count)