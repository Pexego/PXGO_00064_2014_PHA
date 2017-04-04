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
        docargs = {
            'doc_ids': data['ids'],
            'doc_model': report.model,
            'docs': self.env[report.model].browse(data['ids']),
            'gtin': data.get('gtin', False),
        }
        return report_obj.render('quality_protocol_report.report_mrp_label', docargs)
