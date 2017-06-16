# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    duration_type = fields.Selection(selection=[
        ('exact', 'Exact'),
        ('end_month', 'End of month'),
        ('end_year', 'End of year')
    ], default='exact')

    def init(self, cr):
        cr.execute("""update product_template set duration_type = 'exact'
                      where duration_type is null;""")
