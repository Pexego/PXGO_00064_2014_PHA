# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, api, _
from openerp.exceptions import Warning


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def check_pricelist(self):
        self.ensure_one()

        pricelist = self.pricelist_id.version_id.filtered('active')
        if not pricelist:
            raise Warning('There is no pricelist selected')

        messages = []
        orphans = []

        if self.commercial_discount_percentage != self.partner_id.commercial_discount:
            messages.append((0, 0, {
                'type': 'com_discount',
                'description': _('[DifferentDiscounts] - The applied commercial '
                                 'discount (%.2f) differs from that specified '
                                 'in the customer form.\n') %
                               (self.commercial_discount_percentage)
            }))

        if self.financial_discount_percentage != self.partner_id.financial_discount:
            messages.append((0, 0, {
                'type': 'fin_discount',
                'description': _('[DifferentDiscounts] - The applied financial '
                                 'discount (%.2f) differs from that specified '
                                 'in the customer form.\n') %
                               (self.financial_discount_percentage)
            }))

        for item in self.order_line:
            pl_price = pricelist.items_id.filtered(lambda r: r.product_id ==
                                                             item.product_id)
            if not pl_price:
                messages.append((0, 0, {
                    'type': 'not_in_pl',
                    'description': _('[NotInPriceList] - %s - The product is '
                                     'not in %s price list.\n') %
                                   (item.product_id.name_template,
                                    self.pricelist_id.name),
                    'order_line_id': item.id
                }))
                orphans.append(item)

        for item in self.order_line:
            if item not in orphans:
                pl_price = pricelist.items_id.filtered(lambda r: r.product_id ==
                                                                 item.product_id)
                diff = pl_price.price_surcharge - item.price_unit
                diff = float('{0:.5f}'.format(diff))
                if diff != 0:
                    messages.append((0, 0, {
                        'type': 'price',
                        'description': _('[DifferentPrice] - Diff. %.5f - %s - '
                                         'The price of product in the order is '
                                         '%.5f, while in %s price list is %.5f\n') %
                                       (diff,
                                        item.product_id.name_template,
                                        item.price_unit,
                                        self.pricelist_id.name,
                                        pl_price.price_surcharge),
                        'order_line_id': item.id
                    }))

        for item in self.order_line:
            tax_ids = self.partner_id.\
                    property_account_position.map_tax(item.product_id.taxes_id)
            if item not in orphans and item.tax_id != tax_ids:
                tax_names = ', '.join(r.name for r in tax_ids)
                messages.append((0, 0, {
                    'type': 'vat',
                    'description': _('[DifferentVAT] - %s - The product '
                                     'has different tax from %s.\n') %
                                   (item.product_id.name_template, tax_names),
                    'order_line_id': item.id
                }))

        message = self.env['check.pricelist.message'].create({
            'sale_id': self.id,
            'warning_ids': messages
        })

        view = self.env.ref('check_pricelist_ph.check_pricelist_message_wizard')
        return {
            'name': message.title,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'res_model': 'check.pricelist.message',
            'res_id': message.id,
            'target': 'new',
        }
