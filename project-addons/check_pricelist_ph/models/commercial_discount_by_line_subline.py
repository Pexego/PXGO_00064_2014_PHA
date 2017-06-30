# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class CommercialDiscountByLineSubline(models.Model):
    _name = 'commercial.discount.by.line.subline'
    _order = 'line_id, subline_id'

    partner_id = fields.Many2one(comodel_name='res.partner')
    line_id = fields.Many2one(comodel_name='product.line')
    subline_id = fields.Many2one(comodel_name='product.subline')
    discount = fields.Float()