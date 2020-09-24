# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class SaleFromCatalog(models.TransientModel):
    _name = 'sale.from.catalog'

    sale_order_id = fields.Many2one('sale.order')
    item_ids = fields.One2many(comodel_name='sale.from.catalog.items',
                               inverse_name='wizard_id')

    @api.model
    def create(self, vals):
        line_subline_wizard_id = vals.pop('line_subline_wizard_id', False)
        line = vals.pop('line', False)
        subline = vals.pop('subline', False)
        product_ids = self.env['sale.from.line.subline.products'].search([
            ('wizard_id', '=', line_subline_wizard_id),
            ('line', '=', line),
            ('subline', '=', subline),
        ], order='product_name')
        if product_ids:
            item_ids = []
            for prod_id in product_ids:
                item_ids += [(0, 0, {
                    'product_id': prod_id.product_id.id,
                    'line': line,
                    'subline': subline,
                    'qty': 0,
                    'sample': 0,
                    'packing': prod_id.product_id.packing,
                    'box_elements': prod_id.product_id.box_elements,
                })]
            vals['item_ids'] = item_ids
        else:
            raise exceptions.Warning(
                _('Sale from catalog wizard'),
                _('It is not possible to obtain the price list of the sale order')
            )
        return super(SaleFromCatalog, self).create(vals)


class SaleFromCatalogItems(models.TransientModel):
    _name = 'sale.from.catalog.items'

    wizard_id = fields.Many2one('sale.from.catalog')
    product_id = fields.Many2one('product.product')
    line = fields.Many2one('product.line')
    subline = fields.Many2one('product.subline')
    image_medium = fields.Binary(related='product_id.image_medium')
    qty = fields.Float(digits=(16,3))
    sample = fields.Float(digits=(16,3))
    packing = fields.Float(digits=(16,2))
    box_elements = fields.Float(digits=(16,2))
    processed = fields.Boolean(default=False)
    qty_available = fields.Float(related='product_id.qty_available')
    virtual_available = fields.Float(related='product_id.virtual_available')
    virtual_conservative = fields.Float(
        related='product_id.virtual_conservative')

    @api.multi
    def action_create_sale_items(self):
        line_ids = []
        for item_id in self.filtered(lambda i: not i.processed):
            if item_id.qty != 0:
                line_ids += [(0, 0, {
                    'product_id': item_id.product_id.id,
                    'product_uom_qty': item_id.qty,
                })]
            if item_id.sample != 0:
                line_ids += [(0, 0, {
                    'product_id': item_id.product_id.id,
                    'product_uom_qty': item_id.sample,
                    'price_unit': 0,
                })]
        self.write({'processed': True})
        if line_ids:
            self[0].wizard_id.sale_order_id.write({
                'order_line': line_ids,
            })
        return {'result': 'OK'}