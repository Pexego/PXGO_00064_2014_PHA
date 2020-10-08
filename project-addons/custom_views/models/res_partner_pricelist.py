# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class ResPartnerPricelistItem(models.TransientModel):
    _name = 'res.partner.pricelist.item'

    pricelist_id = fields.Many2one(comodel_name='res.partner.pricelist')
    default_code = fields.Char(string='Referencia')
    name = fields.Char(string='Producto')
    sale_price = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        string='Precio de venta'
    )
    product_cost = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        string='Precio de coste'
    )
    product_cost_eval = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'),
        string='Precio coste escandallo'
    )


class ResPartnerPricelist(models.TransientModel):
    _name = 'res.partner.pricelist'

    name = fields.Char(compute='_get_name')
    product_pricelist_id = fields.Many2one(
        comodel_name='product.pricelist', domain="[('type', '=', 'sale')]",
        string='Lista de precios'
    )
    item_ids = fields.One2many(comodel_name='res.partner.pricelist.item',
                               inverse_name='pricelist_id')

    @api.multi
    def _get_name(self):
        for pl in self:
            pl.name = pl.product_pricelist_id.name if pl.product_pricelist_id \
                                                   else ''

    def _get_items(self, pricelist_id):
        item_ids = []
        pricelist_id = self.env['product.pricelist'].browse(pricelist_id)
        for item_id in pricelist_id.version_id[0].items_id:
            product_id = item_id.product_id
            item_ids += [(0, 0, {
                'default_code': product_id.default_code,
                'name': product_id.name,
                'sale_price': item_id.price_surcharge,
                'product_cost': product_id.standard_price,
                'product_cost_eval': product_id.cost_eval_price
            })]
        return item_ids

    @api.model
    def create(self, vals):
        pricelist_id = vals.get('product_pricelist_id')
        if pricelist_id:
            vals['item_ids'] = self._get_items(pricelist_id)
        return super(ResPartnerPricelist, self).create(vals)

    @api.multi
    def write(self, vals):
        pricelist_id = vals.get('product_pricelist_id')
        if pricelist_id:
            vals['item_ids'] = [(5, 0, 0)] + self._get_items(pricelist_id)
        return super(ResPartnerPricelist, self).write(vals)
