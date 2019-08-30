# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class BananasCustomerRate(models.Model):

    _name = 'bananas.customer.rate'

    partner_id = fields.Many2one('res.partner')
    product_id = fields.Many2one('product.product')
    last_sync_price = fields.Float()
    price = fields.Float()

    @api.model
    def calculate(self, partner=False, product=False):
        if partner:
            partners = partner
        else:
            partners = self.env['res.partner'].search(
                [('bananas_synchronized', '=', True)])
        if product:
            products = product
        else:
            products = self.env['product.product'].search(
                [('bananas_synchronized', '=', True)])
        for partner in partners:
            for product in products:
                values = self.env['sale.order.line'].product_id_change_with_wh(
                    partner.property_product_pricelist.id, product.id,
                    qty=1, partner_id=partner.id,
                    fiscal_position=partner.property_account_position.id)
                if 'price_unit' not in values['value'].keys():
                    continue
                price = values['value']['price_unit']
                current_rate = self.env['bananas.customer.rate'].search(
                    [('partner_id', '=', partner.id),
                     ('product_id', '=', product.id)])
                if current_rate:
                    current_rate.write({'price': price})
                else:
                    self.create(
                        {'partner_id': partner.id,
                         'product_id': product.id,
                         'price': price,
                         'last_sync_price': price})
                    continue

    @api.model
    def remove(self, partner=False, product=False):
        domain = []
        if partner:
            domain.append(('partner_id', '=', partner.id))
        if product:
            domain.append(('product_id', '=', product.id))
        self.search(domain).unlink()
