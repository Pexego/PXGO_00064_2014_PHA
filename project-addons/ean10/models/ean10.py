# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _


class Ean10Code(models.Model):
    _name = 'ean10.code'

    name = fields.Char(required=True)

    @api.multi
    def generate_and_search_ean13(self):
        def control_code13(code):
            sum = 0
            for d in range(12):
                sum += int(code[d]) * (1 if d % 2 == 0 else 3)
            return (10 - sum % 10) % 10

        ean13_ids = self.env['ean13.product']
        product_ids = self.env['product.product']
        for pair in range(100):
            control_digit = control_code13('{}{:02d}'.format(self.name, pair))
            ean13 = '{}{:02d}{:d}'.format(self.name, pair, control_digit)
            product_ids = product_ids.search([('ean13', '=', ean13)])
            if product_ids:
                for product_id in product_ids:
                    ean13_ids |= ean13_ids.create({
                        'name': ean13,
                        'product_id': product_id.id,
                        'default_code': product_id.default_code,
                        'country_id': product_id.country.id,
                        'uses': len(product_ids)
                    })
            else:
                ean13_ids |= ean13_ids.create({
                    'name': ean13,
                    'product_id': False,
                    'default_code': False,
                    'country_id': False,
                    'uses': 0
                })

        view_id = self.env.ref('ean10.ean13_tree_view')
        return {
            'name': _('EAN13 codes for %s') % self.name,
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'tree',
            'res_model': 'ean13.product',
            'view_id': view_id.id,
            'target': 'current',
            'domain': [('id','in', ean13_ids.ids)],
        }


class Ean13Product(models.TransientModel):
    _name = 'ean13.product'

    name = fields.Char(readonly=True)
    product_id = fields.Many2one(comodel_name='product.product', readonly=True)
    default_code = fields.Char(readonly=True)
    country_id = fields.Many2one(comodel_name='res.country', readonly=True)
    uses = fields.Integer(readonly=True)
