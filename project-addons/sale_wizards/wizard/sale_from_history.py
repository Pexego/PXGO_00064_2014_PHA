# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class SaleFromHistory(models.TransientModel):
    _name = 'sale.from.history'

    sale_order_id = fields.Many2one('sale.order')
    item_ids = fields.One2many(comodel_name='sale.from.history.items',
                               inverse_name='wizard_id')

    @api.model
    def create(self, vals):
        sale_order_id = vals.get('sale_order_id', False)
        sale_id = self.env['sale.order'].browse(sale_order_id)
        if sale_id and sale_id.pricelist_id:
            pv_item_ids = sale_id.pricelist_id.version_id.items_id
            sale_item_ids = self.env['sale.order.line'].search([
                ('order_id.partner_shipping_id', '=', sale_id.partner_shipping_id.id),
                ('order_id.state', '=', 'done'),
                ('product_id', 'in', pv_item_ids.mapped('product_id').ids),
            ], order='create_date desc, product_id')
            item_ids = []
            for sale_item_id in sale_item_ids:
                found_idx = -1
                for idx, data in enumerate(item_ids):
                    if data[2]['product_id'] == sale_item_id.product_id.id:
                        found_idx = idx
                        break
                if found_idx > -1:
                    if item_ids[found_idx][2]['date'] != sale_item_id.create_date:
                        continue
                    elif sale_item_id.price_unit > 0:
                        item_ids[found_idx][2]['last_qty'] += \
                            sale_item_id.product_uom_qty
                    else:
                        item_ids[found_idx][2]['last_sample'] += \
                            sale_item_id.product_uom_qty
                else:
                    # Show only the first 80 products
                    if len(item_ids) == 80:
                        break
                    else:
                        item_ids += [(0, 0, {
                            'date': sale_item_id.create_date,
                            'product_id': sale_item_id.product_id.id,
                            'line': sale_item_id.product_id.line.id,
                            'subline': sale_item_id.product_id.subline.id,
                            'last_qty': sale_item_id.product_uom_qty \
                                if sale_item_id.price_unit > 0 else 0,
                            'last_sample': sale_item_id.product_uom_qty \
                                if sale_item_id.price_unit <= 0 else 0,
                            'packing': sale_item_id.product_id.packing,
                            'box_elements': sale_item_id.product_id.box_elements,
                        })]
            vals['item_ids'] = item_ids
        res = super(SaleFromHistory, self).create(vals)
        return res


class SaleFromHistoryItems(models.TransientModel):
    _name = 'sale.from.history.items'

    wizard_id = fields.Many2one('sale.from.history')
    date = fields.Datetime()
    product_id = fields.Many2one('product.product')
    line = fields.Many2one('product.line')
    subline = fields.Many2one('product.subline')
    image_medium = fields.Binary(related='product_id.image_medium')
    qty = fields.Float(digits=(16,3))
    sample = fields.Float(digits=(16,3))
    last_qty = fields.Float(digits=(16, 3))
    last_sample = fields.Float(digits=(16, 3))
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

    @api.multi
    def action_copy_quantities(self):
        self.ensure_one()
        return self.write({
            'qty': self.last_qty,
            'sample': self.last_sample
        })