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

    # Url que se genera desde el wizard de impresión de protocolo, recive producción y protocolo como parámetros
    # Los parámetros se recien de la forma <tipo_de_dato:nombre_de_parametro>
    @http.route(['/protocol/print/<model("mrp.production"):production>/<model("quality.protocol.report"):protocol>'],
                type='http', auth='public', website=True)
    def print_survey(self, production, protocol, **post):
        context = {'production': production}
        seq = 1
        # Se generar un surveyX por cada survey en el protocolo, luego la plantilla se encargará de parsear para cada uno el parámetro survey, que es el que usa internamente la vista genérica
        parts = []
        for line in protocol.report_line_ids:
            if line.survey_id:
                #context.update({'survey' + str(seq): line.survey_id})
                #seq += 1
                parts.append(('s',line.survey_id))
            elif line.view_id:
                parts.append(('v',line.view_id.xml_id))
        context.update({'parts': parts})
        # renderiza la vista qweb con id protocol_print, de este módulo, pasándole en contexto production y tantos surveyX como surveys en el protocolo
        return request.website.render('quality_protocol_report.protocol_print',
                                      context)
