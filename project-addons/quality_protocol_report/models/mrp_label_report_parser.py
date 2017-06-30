# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class MrpLabelReport(models.AbstractModel):

    _name = 'report.quality_protocol_report.report_mrp_label'

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        report = report_obj._get_report_from_name('quality_protocol_report.report_mrp_label')
        doc = self.env[report.model].browse(data['ids'])
        name_css_size = 52
        if len(doc.product_id.name) > 51:
            name_css_size = 22
        elif len(doc.product_id.name) > 39:
            name_css_size = 32
        elif len(doc.product_id.name) > 31:
            name_css_size = 42

        lot_css_size = 140
        if len(doc.final_lot_id.name) > 14:
            lot_css_size = 90
        elif len(doc.final_lot_id.name) > 11:
            lot_css_size = 110

        docargs = {
            'doc_ids': data['ids'],
            'doc_model': report.model,
            'docs': doc,
            'gtin': data.get('gtin', False),
            'name_css_size': str(name_css_size),
            'lot_css_size': str(lot_css_size)
        }
        return report_obj.render('quality_protocol_report.report_mrp_label', docargs)
