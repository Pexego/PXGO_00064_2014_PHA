# -*- coding: utf-8 -*-
from openerp import models, api


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    @api.multi
    def action_edit_analysis(self):
        view_id = self.env.ref('editable_reports.stock_lot_analysis')
        return self.editable_report_form(view_id.id)
