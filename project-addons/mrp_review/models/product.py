# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _


class ProductCategory(models.Model):

    _inherit = 'product.category'

    needs_mrp_review = fields.Boolean()
