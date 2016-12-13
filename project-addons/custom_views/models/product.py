# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus All Rights Reserved
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
    manufacture_protocol = fields.Char('Manufacture protocol')
    manufacture_proto_ver = fields.Char('Manufacture protocol version')
    second_conditioning_protocol = fields.Char('Secondary conditioning protocol')
    second_conditioning_proto_ver = fields.Char('Sec. conditioning proto. version')

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

    @api.one
    @api.depends('qty_available', 'outgoing_qty')
    def _virtual_conservative(self):
        self.virtual_conservative = self.qty_available - self.outgoing_qty


class PricelistPartnerinfo(models.Model):
    _inherit = 'pricelist.partnerinfo'

    sequence = fields.Integer(related='suppinfo_id.sequence')