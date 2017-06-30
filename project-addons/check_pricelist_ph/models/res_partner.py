# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    com_discount_by_line_subline_id = fields.One2many(
        string='Check pricelist multi comm. discount',
        comodel_name='commercial.discount.by.line.subline',
        inverse_name='partner_id',
        help='Only for sale orders check pricelist button. When a customer has '
             'defined these discounts, will be applied according to the line '
             'and subline of each product. If, in the same order, the products '
             'have different line or subline, a discount of 0%. If none is '
             'defined, the general commercial discount is used.'
    )
