# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import openerp.addons.decimal_precision as dp
import datetime

class ProductProduct(models.Model):
    _inherit = 'product.product'

    is_in_current_pricelist = fields.Boolean(
            compute='_compute_is_in_current_pricelist',
            search='_search_is_in_current_pricelist')
    year_appearance = fields.Integer('Year of appearance',
                                     default=datetime.datetime.now().year)
    manufacturing_procedure_id = fields.Many2one(comodel_name='mrp.procedure',
                              domain="[('type_id.code', '=', 'product_manufacturing')]",
                              string='Manufacturing procedure')
    packaging_procedure_id = fields.Many2one(comodel_name='mrp.procedure',
                                  domain="[('type_id.code', '=', 'product_packaging')]",
                                  string='Packaging procedure')

    @api.one
    @api.constrains('year_appearance')
    def _check_year_of_appearance(self):
        current_year = datetime.datetime.now().year
        if 1956 >= self.year_appearance <= current_year:
            raise Warning(_('Year must be between 1956 and %s.') %
                          (current_year,))

    @api.multi
    def name_get(self): # Hide default_code by default
        return super(ProductProduct,
                     self.with_context(display_default_code=False)).name_get()

    @api.depends('pricelist_id')
    def _compute_is_in_current_pricelist(self):
        pricelist = self.pricelist_id.mapped('id')
        return self.env.context.get('pricelist', False) in pricelist

    def _search_is_in_current_pricelist(self, operator, value):
        # This domain filter by price list is only for Pharmadus and
        # sale orders that aren't for sample/advertising purposes
        if (self.env.user.company_id != self.env.ref('base.main_company')) or\
                self.env.context.get('is_a_sample_order', False):
            return [('active', '=', True)]

        current_pricelist_product_list = []
        pricelist = self.env.context.get('pricelist', False)
        if pricelist:
            pricelist_id = self.env['product.pricelist'].browse(pricelist)
            current_pricelist_product_list = \
                pricelist_id.version_id.items_id.mapped('product_id.id')
        if ((operator == '=') and value) or ((operator == '!=') and not value):
            operator = 'in'
        else:
            operator = 'not in'
        return [('id', operator, current_pricelist_product_list)]


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    suppliers_pricelists = fields.One2many('pricelist.partnerinfo',
                                 compute='_suppliers_pricelists')
    cost_price_rm = fields.Float('Raw material cost price',
                                 digits=dp.get_precision('Product Price'))
    cost_price_components = fields.Float('Components cost price',
                                 digits=dp.get_precision('Product Price'))
    cost_price_dl = fields.Float('Direct labor cost price',
                                 digits=dp.get_precision('Product Price'))
    internal_scrapped_qty = fields.Float('Stock at internal scrap location',
                           compute = '_internal_scrapped',
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly = True)
    virtual_conservative = fields.Float('Virtual stock conservative',
                           compute='_virtual_conservative',
                           digits = dp.get_precision('Product Unit of Measure'),
                           readonly=True)

    @api.one
    @api.depends('seller_ids')
    def _suppliers_pricelists(self):
        ids = []
        for product in self:
            for seller in product.seller_ids:
                for pricelist in seller.pricelist_ids:
                    ids.append(pricelist.id)
        self.suppliers_pricelists = ids

    @api.multi
    def _internal_scrapped(self):
        for product in self:
            quants = self.env['stock.quant'].search([
                ('product_id.product_tmpl_id', '=', product.id),
                ('location_id.usage', '=', 'internal'),
                ('location_id.scrap_location', '=', True)
            ])
            product.internal_scrapped_qty = sum(quant.qty for quant in quants)

    @api.one
    @api.depends('qty_available', 'outgoing_qty', 'internal_scrapped_qty')
    def _virtual_conservative(self):
        self.virtual_conservative = self.qty_available - self.outgoing_qty - \
                                    self.internal_scrapped_qty


class PricelistPartnerinfo(models.Model):
    _inherit = 'pricelist.partnerinfo'

    sequence = fields.Integer(related='suppinfo_id.sequence')