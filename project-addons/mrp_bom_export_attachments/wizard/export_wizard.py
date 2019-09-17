# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _, tools
from openerp.exceptions import Warning
from os.path import splitext
from shutil import rmtree
import os, base64, sys, tempfile, zipfile, time
from datetime import datetime, timedelta


class BomAttachmentsExportWizard(models.TransientModel):
    _name = 'bom.attachments.export.wizard'

    name = fields.Char(compute='_get_filename')

    @api.one
    def _get_filename(self):
        self.name = 'bom_attachments.zip'


    @api.multi
    def export_attachments(self):
        location = tempfile.mkdtemp()
        if not os.path.isdir(location):
            raise Warning(_('Invalid location'),
                          _('The specified location does not exists'))
        if location[-1:] != '/':
            location += '/'

        def normalize(txt):
            return txt.encode(sys.getfilesystemencoding())

        def zipdir(path, ziph):  # ziph is zipfile handle
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_full_path = os.path.join(root, file)
                    file_relative_path = file_full_path.replace(path, '')
                    ziph.write(file_full_path, file_relative_path)

        ir_attachment = self.env['ir.attachment']
        for bom_id in self.env['mrp.bom'].search([]):
            attachment_ids = ir_attachment.search([('res_model', '=', 'mrp.bom'),
                                                   ('res_id', '=', bom_id.id)])
            if attachment_ids:
                prod_id = bom_id.product_id
                line = prod_id.line.name.replace('/', '') \
                    if prod_id.line else 'sin-linea'
                subline = prod_id.subline.name.replace('/', '') \
                    if prod_id.subline else 'sin-sublinea'
                container = prod_id.container_id.name.replace('/', '') \
                    if prod_id.container_id else 'sin-envasado'
                base_form = prod_id.base_form_id.name.replace('/', '') \
                    if prod_id.base_form_id else 'sin-forma-base'
                if prod_id.clothing == 'dressed':
                    clothing = 'vestida'
                elif prod_id.clothing == 'naked':
                    clothing = 'desnuda'
                else:
                    clothing = 'sin-vestimenta'
                qty = int(prod_id.qty) if prod_id.qty else 'sin-cantidad'

                loc = normalize(location + line)
                if not os.path.exists(loc):
                    os.mkdir(loc)
                loc = normalize(location + line + '/' + subline)
                if not os.path.exists(loc):
                    os.mkdir(loc)
                end_path = u'{}{}/{}/{}_{}_{}_{}'.format(location, line, subline,
                           container, base_form, clothing, qty)
                end_path = normalize(end_path)
                if not os.path.exists(end_path):
                    os.mkdir(end_path)

                counter = 1
                for att_id in attachment_ids:
                    filename, extension = splitext(att_id.name)
                    filename = prod_id.name.replace('/', '-')
                    reference = prod_id.default_code
                    suffix = '0{}'.format(counter)[-2:]
                    filename = u'{} [{}] ({}){}'.format(filename, reference,
                                                        suffix, extension)
                    filename = normalize(filename)
                    filename = '{}/{}'.format(end_path, filename)
                    f = open(filename, 'wb')
                    f.write(base64.b64decode(att_id.datas))
                    f.close()
                    counter += 1

        zf = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        zf = zf.replace('/wizard', '/static/bom_attachments.zip')
        if os.path.isfile(zf):
            os.unlink(zf)
        zipf = zipfile.ZipFile(zf, 'w', zipfile.ZIP_DEFLATED)
        zipdir(location, zipf)
        zipf.close()

        rmtree(location, ignore_errors=True)

        # Activate programmed task to free zip file occupied space
        if os.path.getsize(zf) > 0:
            self.env.ref('mrp_bom_export_attachments.empty_zip_file').sudo().\
                write({
                    'active': True,
                    'nextcall': (datetime.now() + timedelta(hours=1)).
                        strftime(tools.DEFAULT_SERVER_DATETIME_FORMAT)
                })

        return {
            'type': 'ir.actions.act_url',
            'url': '/mrp_bom_export_attachments/static/bom_attachments.zip',
            'target': 'self',
        }

    @api.multi
    def empty_zip_file(self):
        zf = os.path.join(os.path.dirname(os.path.abspath(__file__)))
        zf = zf.replace('/wizard', '/static/bom_attachments.zip')
        an_hour_ago = time.time() - 1*60*60
        if os.path.getsize(zf) > 0 and os.path.getmtime(zf) < an_hour_ago:
            f = open(zf, 'wb+')
            f.truncate(0)
            f.close()
            # Deactivate programmed task
            self.env.ref('mrp_bom_export_attachments.empty_zip_file').sudo().\
                write({'active': False})