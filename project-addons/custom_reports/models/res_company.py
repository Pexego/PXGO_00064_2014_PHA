# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    report_header_message = fields.Text(translate=True)
    report_sales_footer_message = fields.Text(translate=True)
    report_purchases_footer_message = fields.Text(translate=True)
    report_gdpr_footer_message = fields.Text(translate=True)
    report_waste_disposal_footer_message = fields.Text(translate=True)
    report_sales_email = fields.Char(translate=True)
    report_purchases_email = fields.Char(translate=True)
    report_product_category_message = fields.One2many(
        comodel_name='report.product.category.message',
        inverse_name='company_id')
