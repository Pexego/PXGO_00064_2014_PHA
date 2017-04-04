# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    product_ids = fields.Many2many(string='Products',
                                   comodel_name='product.template',
                                   relation='product_mrp_routing_rel',
                                   column1='routing_id',
                                   column2='product_id')