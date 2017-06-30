# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    com_discount_by_line_subline_id = fields.One2many(
        comodel_name='commercial.discount.by.line.subline',
        inverse_name='partner_id')
