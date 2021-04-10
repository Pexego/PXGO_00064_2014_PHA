# -*- coding: utf-8 -*-
from openerp.addons.web import http
from openerp.addons.web.http import request


class WebsiteEditableReport(http.Controller):
    @http.route(['/editable_report/print/<model("ir.ui.view"):view_id>/<record_id>'],
                type='http', auth='user', website=True)
    def print_editable_report(self, view_id, record_id, **post):
        cr, uid, original_context, session = \
            request.cr, request.uid, request.context, request.session
        record_id = request.registry[view_id.model].\
            browse(cr, uid, int(record_id), original_context)
        context = {
            'view_id': view_id,
            'record_id': record_id
        }
        # Renderiza la vista qweb
        return request.website.render('editable_reports.report_print', context)
