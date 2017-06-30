# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    finished_dest_location_id = fields.Many2one('stock.location',
                                                'Finished products location')
