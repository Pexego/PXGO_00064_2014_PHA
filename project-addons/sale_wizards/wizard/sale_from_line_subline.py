# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class SaleFromLineSubline(models.TransientModel):
    _name = 'sale.from.line.subline'

    sale_order_id = fields.Many2one('sale.order')
    item_ids = fields.One2many(comodel_name='sale.from.line.subline.items',
                               inverse_name='wizard_id')
    product_ids = fields.One2many(comodel_name='sale.from.line.subline.products',
                                  inverse_name='wizard_id')

    @api.model
    def create(self, vals):
        sale_order_id = vals.get('sale_order_id', False)
        sale_order_id = self.env['sale.order'].browse(sale_order_id)
        if sale_order_id and sale_order_id.pricelist_id:
            pl_product_ids = sale_order_id.pricelist_id.version_id.items_id.\
                mapped('product_id')
            product_ids = []
            combinations = {}
            for product_id in pl_product_ids:
                line_id = product_id.line.id
                subline_id = product_id.subline.id
                product_ids += [(0, 0, {
                    'product_id': product_id.id,
                    'line': line_id,
                    'subline': subline_id,
                })]
                if line_id in combinations:
                    if not subline_id in combinations[line_id]:
                        combinations[line_id].append(subline_id)
                else:
                    combinations[line_id] = [subline_id]
            item_ids = []
            for line, sublines in combinations.items():
                for subline in sublines:
                    item_ids += [(0, 0, {
                        'line': line,
                        'subline': subline,
                    })]
            vals['item_ids'] = item_ids
            vals['product_ids'] = product_ids
        res = super(SaleFromLineSubline, self).create(vals)
        return res


class SaleFromLineSublineItems(models.TransientModel):
    _name = 'sale.from.line.subline.items'

    wizard_id = fields.Many2one('sale.from.line.subline')
    line = fields.Many2one('product.line')
    subline = fields.Many2one('product.subline')

    @api.multi
    def action_show_products(self):
        wizard_id = self.env['sale.from.catalog'].create({
            'sale_order_id': self.wizard_id.sale_order_id.id,
            'line': self.line.id,
            'subline': self.subline.id,
            'line_subline_wizard_id': self.wizard_id.id,
        })
        return {
            'type': 'ir.actions.act_window',
            'name': 'Sale from catalog wizard',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'sale.from.catalog.items',
            'domain': [('wizard_id', '=', wizard_id.id)],
            'view_id': self.env.ref('sale_wizards.sale_from_catalog_wizard').id,
            'target': 'current',
        }


class SaleFromLineSublineProducts(models.TransientModel):
    _name = 'sale.from.line.subline.products'

    wizard_id = fields.Many2one('sale.from.line.subline')
    product_id = fields.Many2one('product.product')
    line = fields.Many2one('product.line')
    subline = fields.Many2one('product.subline')
