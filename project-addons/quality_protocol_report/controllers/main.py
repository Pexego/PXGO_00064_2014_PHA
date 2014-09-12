# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.addons.web import http
from openerp.addons.web.http import request


class WebsiteProtocol(http.Controller):

    # Printing routes
    @http.route(['/protocol/print/<model("mrp.production"):production>/<model("quality.protocol.report"):protocol>'],
                type='http', auth='public', website=True)
    def print_survey(self, production, protocol, **post):
        context = {'production': production}
        seq = 1
        for line in protocol.report_line_ids:
            if line.survey_id:
                context.update({'survey' + str(seq): line.survey_id})
                seq += 1
        return request.website.render('quality_protocol_report.protocol_print',
                                      context)
