# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from os.path import splitext
import os, base64, sys


class BomAttachmentsExportWizard(models.TransientModel):
    _name = 'bom.attachments.export.wizard'

    location = fields.Char('Location where directory structure will be generated')

    @api.multi
    def export_attachments(self):
        if not os.path.isdir(self.location):
            raise Warning(_('Invalid location'),
                          _('The specified location does not exists'))
        location = self.location
        if location[-1:] != '/':
            location += '/'

        def normalize(txt):
            return txt.encode(sys.getfilesystemencoding())

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
                    suffix = '0{}'.format(counter)[-2:]
                    filename = u'{} [{}]{}'.format(filename, suffix, extension)
                    filename = normalize(filename)
                    filename = '{}/{}'.format(end_path, filename)
                    f = open(filename, 'wb')
                    f.write(base64.b64decode(att_id.datas))
                    f.close()
                    counter += 1

        return True