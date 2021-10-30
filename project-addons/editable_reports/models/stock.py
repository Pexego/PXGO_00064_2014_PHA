# -*- coding: utf-8 -*-
from openerp import models, api

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    def action_edit_analysis(self):
        view_id = self.env.ref('editable_reports.stock_lot_analysis')
        target_id = self.lot_id.id if self.lot_id else False
        return self.editable_report_form(view_id.id, target_id)