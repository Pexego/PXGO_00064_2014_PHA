# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api
import datetime
import calendar


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.model
    def _get_use_date(self):
        product_id = self.env.context.get('product_id', False)
        if product_id:
            product = self.env['product.product'].browse(product_id)
            date = datetime.datetime.today() + \
                   datetime.timedelta(days=product.use_time)
            if product.duration_type == 'end_month':
                date = date + datetime.timedelta(days=calendar.
                            monthrange(date.year, date.month)[1] - date.day)
            elif product.duration_type == 'end_year':
                date = datetime.date(date.year, 12, 31)

            return date and fields.Datetime.to_string(date) or False
        else:
            return False

    use_date = fields.Datetime(default=_get_use_date)
    duration_type = fields.Selection(selection=[
        ('exact', 'Exact'),
        ('end_month', 'End of month'),
        ('end_year', 'End of year')
    ], default=lambda r: r.product_id.duration_type)

    def init(self, cr):
        cr.execute("""update stock_production_lot set duration_type = 'exact'
                      where duration_type is null;""")