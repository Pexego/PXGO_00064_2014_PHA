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
import unicodedata
from urlparse import urljoin
from pyPdf import PdfFileWriter, PdfFileReader
from contextlib import closing
from openerp import models, fields, api, exceptions, _
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
            obj = self.env['mrp.production'].search(
                [('final_lot_id', '=', self.env.context['active_id'])])
        else:
            obj = self.env[self.env.context['active_model']].browse(
                self.env.context['active_id'])

        use_protocol = False
        for workcenter_line in obj.workcenter_lines:
            protocol_link = obj.product_id.protocol_ids.filtered(
                lambda r: r.protocol.type_id.group_print and
                          r.protocol.type_id.id ==
                          workcenter_line.workcenter_id.protocol_type_id.id)
            use_protocol = protocol_link.filtered(
                lambda r: obj.routing_id == r.route and obj.bom_id == r.bom)
            if not use_protocol:
                use_protocol = protocol_link.filtered(
                    lambda r: obj.routing_id == r.route or obj.bom_id == r.bom)
            if not use_protocol:
                use_protocol = protocol_link.filtered(
                    lambda r: not r.route and not r.bom)
            if not use_protocol:
                continue
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
            weight = workcenter_line.workcenter_id.protocol_type_id.weight
            production_name = obj.display_name
            protocol_type_id = workcenter_line.workcenter_id.protocol_type_id
            protocol_type = protocol_type_id.name
            if protocol_type_id.is_continuation:
                protocol_type += fields.Datetime. \
                    from_string(workcenter_line.create_date).strftime(' %d-%m-%Y')
            protocol_name = unicodedata.normalize('NFKD', use_protocol.name). \
                encode('ascii', 'ignore').replace(' ', '~')
            protocol_type = unicodedata.normalize('NFKD', protocol_type). \
                encode('ascii', 'ignore').replace(' ', '~')
            product_name = obj.product_id.display_name
            product_name = unicodedata.normalize('NFKD', product_name). \
                               encode('ascii', 'ignore').replace(' ', '~')[0:50]
            lot_name = obj.final_lot_id.display_name
            lot_name = unicodedata.normalize('NFKD', lot_name). \
                encode('ascii', 'ignore').replace(' ', '~')
            date_planned = fields.Datetime.from_string(obj.date_planned). \
                strftime('%d-%m-%Y')

            res.append(
                urljoin(
                    base_url,
                    "protocol/print/%s/%s/%s?weight=%02d#prod=%s#protname=%s#"
                    "prot=%s#product=%s#lot=%s#date=%s" % (
                        slug(obj),
                        slug(use_protocol),
                        slug(workcenter_line),
                        weight,
                        production_name,
                        protocol_name,
                        protocol_type,
                        product_name,
                        lot_name,
                        date_planned
                    )
                )
            )
        return res

    def _merge_pdf(self, documents):
        """Merge PDF files into one.

        :param documents: list of path of pdf files
        :returns: path of the merged pdf
        """
        writer = PdfFileWriter()
        streams = []
        for document in documents:
            pdfreport = file(document, 'rb')
            streams.append(pdfreport)
            reader = PdfFileReader(pdfreport)
            for page in range(0, reader.getNumPages()):
                writer.addPage(reader.getPage(page))

        merged_file_fd, merged_file_path = tempfile.mkstemp(
            suffix='.pdf', prefix='report.merged.tmp.')
        with closing(os.fdopen(merged_file_fd, 'w')) as merged_file:
            writer.write(merged_file)

        for stream in streams:
            stream.close()

        return merged_file_path

    @api.multi
    def print_all(self):
        """
            Se llama al script static/src/js/get_url_pdf.js
            con los argumentos session_id, directorio donde guardar,
            urls que crea 1 pdf por cada url
            Luego se hace merge de los pdf desde esta parte.
        """
        if not request:
            raise exceptions.Warning(_(''), _(''))
        session_id = request.session.sid
        config = self.env['ir.config_parameter']
        addons_url = config.get_param('addons_path')
        phantomjs_path = config.get_param('phantomjs_path')
        phantomjs_path = 'phantomjs' if not phantomjs_path else phantomjs_path
        print_url = self.env.context.get('protocol_url', False)
        if print_url:
            print_urls = [print_url]
        else:
            print_urls = self._get_print_urls()
        if not print_urls:
            return
        phantom = [
            phantomjs_path,
            addons_url +
            '/quality_protocol_report/static/src/js/phantom_url_to_pdf.js',
            session_id, "/tmp"] + print_urls
        process = subprocess.Popen(phantom)
        process.communicate()
        filenames = []
        for url in print_urls:
            fname = url.replace('/', '').replace(':', '')
            weight_pos = fname.find('?weight=')
            if weight_pos > -1:
                fname = fname[weight_pos+8:weight_pos+10] + '-' + fname[:weight_pos]
            filenames.append('/tmp/' + fname + '.pdf')
        filepath = self._merge_pdf(sorted(filenames))
        fildecode = open(filepath, 'r')
        encode_data = fildecode.read()
        fildecode.close()
        attachment_data = {
            'name': 'quality_protocol.pdf' if print_url else 'quality_protocols' +
                str(self.env.context.get('active_id', '')) + '.pdf',
            'datas_fname': 'quality_protocols' +
                str(self.env.context.get('active_id', '')) + '.pdf',
            'datas': base64.b64encode(encode_data),
            'res_model': self.env.context.get('active_model', False),
            'res_id': 0 if print_url else self.env.context.get('active_id', False),
        }
        self.env['ir.attachment'].search(
            [('name', '=', attachment_data['name']),
             ('res_id', '=', attachment_data['res_id']),
             ('res_model', '=', attachment_data['res_model'])]).unlink()
        attachment = self.env['ir.attachment'].create(attachment_data)

        filenames.append(filepath)
        for my_file in filenames:
            os.remove(my_file)

        if print_url:
            return {
                'type': 'ir.actions.act_url',
                'url': '/web/binary/saveas?model=ir.attachment&field=datas' +
                       '&filename_field=name&id=%s' % (attachment.id),
                'target': 'self',
            }
        else:
            return {'type': 'ir.actions.act_window_close'}
