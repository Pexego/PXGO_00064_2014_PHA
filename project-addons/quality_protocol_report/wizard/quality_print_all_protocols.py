# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
import subprocess
import tempfile
import os
import base64
from urlparse import urljoin
from pyPdf import PdfFileWriter, PdfFileReader
from contextlib import closing
from openerp import models, api, exceptions, _
from openerp.addons.website.models.website import slug
from openerp.addons.web.http import request


class QualityReportAll(models.TransientModel):

    _name = 'quality.report.all'

    def _get_print_urls(self):
        res = []
        if self.env.context.get('relative_url'):
            base_url = '/'
        else:
            base_url = self.env['ir.config_parameter'].\
                get_param('web.base.url')
        if self.env.context['active_model'] == u'stock.production.lot':
            obj_id = self.env['mrp.production'].search([('final_lot_id', '=', self.env.context['active_id'])])
        else:
            obj = self.env[self.env.context['active_model']].browse(self.env.context['active_id'])

        use_protocol = False
        for workcenter_line in obj.workcenter_lines:
            protocol_link = obj.product_id.protocol_ids.filtered(lambda r: r.protocol.type_id.id == workcenter_line.workcenter_id.protocol_type_id.id)
            use_protocol = protocol_link.filtered(lambda r: obj.routing_id == r.route and obj.bom_id == r.bom)
            if not use_protocol:
                use_protocol = protocol_link.filtered(lambda r: obj.routing_id == r.route or obj.bom_id == r.bom)
            if not use_protocol:
                use_protocol = protocol_link.filtered(lambda r: not r.route and not r.bom)
            if not use_protocol:
                raise exceptions.Warning(_('Not found'), _('Protocol not found for the product %s.') % obj.product_id.name)
            else:
                use_protocol = use_protocol.protocol
            if not workcenter_line.realized_ids:
                for line in use_protocol.report_line_ids:
                    if line.log_realization:
                        self.env['quality.realization'].create(
                             {
                                'name': line.name,
                                'workcenter_line_id': workcenter_line.id
                            })
            res.append(urljoin(base_url, "protocol/print/%s/%s/%s" % (slug(obj), slug(use_protocol), slug(workcenter_line))))
        return res

    def _merge_pdf(self, documents):
        """Merge PDF files into one.

        :param documents: list of path of pdf files
        :returns: path of the merged pdf
        """
        writer = PdfFileWriter()
        streams = []  # We have to close the streams *after* PdfFilWriter's call to write()
        for document in documents:
            pdfreport = file(document, 'rb')
            streams.append(pdfreport)
            reader = PdfFileReader(pdfreport)
            for page in range(0, reader.getNumPages()):
                writer.addPage(reader.getPage(page))

        merged_file_fd, merged_file_path = tempfile.mkstemp(suffix='.pdf', prefix='report.merged.tmp.')
        with closing(os.fdopen(merged_file_fd, 'w')) as merged_file:
            writer.write(merged_file)

        for stream in streams:
            stream.close()

        return merged_file_path

    @api.multi
    def print_all(self):
        """
            Se llama al script static/src/js/get_url_pdf.js con los argumentos session_id, directorio donde guardar, urls que crea 1 pdf por cada url
            Luego se hace merge de los pdf desde esta parte.
        """
        if not request:
            raise exceptions.Warning(_(''), _(''))
        session_id = request.session.sid
        addons_url = self.env['ir.config_parameter'].get_param('addons_path')
        phantom = ["phantomjs", addons_url + "/quality_protocol_report/static/src/js/phantom_url_to_pdf.js", session_id, "/tmp"] + self._get_print_urls()
        process = subprocess.Popen(phantom)
        output = process.communicate()
        filenames = []
        for url in self._get_print_urls():
            filenames.append('/tmp/' + url.replace('/', '').replace(':', '') + '.pdf')
        filepath = self._merge_pdf(filenames)
        fildecode=open(filepath,"r")
        encode_data = fildecode.read()
        fildecode.close()
        attachment_data = {
                    'name': 'quality_protocols' + str(self.env.context.get('active_id', '')) + '.pdf',
                    'datas_fname': 'quality_protocols' + str(self.env.context.get('active_id', '')) + '.pdf',
                    'datas': base64.b64encode(encode_data),
                    'res_model': self.env.context.get('active_model', False),
                    'res_id': self.env.context.get('active_id', False),
            }
        self.env['ir.attachment'].search(
            [('name', '=', attachment_data['name']),
             ('res_id', '=', attachment_data['res_id']),
             ('res_model', '=', attachment_data['res_model'])]).unlink()
        self.env['ir.attachment'].create(attachment_data)
        filenames.append(filepath)
        for my_file in filenames:
            os.remove(my_file)
        return {'type': 'ir.actions.act_window_close'}
