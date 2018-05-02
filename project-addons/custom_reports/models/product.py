# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ProductCategory(models.Model):
    _inherit = 'product.category'

    commissions_parent_category = fields.Boolean('Commissions parent category',
                                                 default=False)
    message_ids = fields.Many2many(comodel_name='report.product.category.message',
                                   relation='report_prod_cat_message_rel',
                                   column1='categ_id', column2='message_id',
                                   string='Messages to show in reports')
