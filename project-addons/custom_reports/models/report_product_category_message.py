# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ReportProductCategoryMessage(models.Model):
    _name = 'report.product.category.message'
    _description = 'Report product category message'

    name = fields.Text(string='Message')
    company_id = fields.Many2one(comodel_name='res.company',
                                 default=lambda rec: rec.env.user.company_id)
    categ_ids = fields.Many2many(comodel_name='product.category',
                                 relation='report_prod_cat_message_rel',
                                 column1='message_id', column2='categ_id',
                                 string='Categories to show message')