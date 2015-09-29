# -*- coding: utf-8 -*-
# #############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
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
##############################################################################
#

from openerp import models, fields, api, _, tools
from openerp.exceptions import Warning
import shutil, os


class res_sales_abroad(models.Model):
    _name = 'res.sales.abroad'
    documents = fields.Char()
    country_id = fields.Many2one('res.country', ondelete='restrict')
    attachments = fields.One2many('ir.attachment', 'sales_abroad_id')

    def unlink(self, cr, uid, ids, context=None):
        # Delete all related attachments before
        attachment = self.env['ir.attachment']
        for sa in self.browse(cr, uid, ids, context=context):
            attachment.unlink(cr, uid, sa.attachments.ids, context=context)

        return super(res_sales_abroad, self).unlink(cr, uid, ids, context=context)

class res_country(models.Model):
    _inherit = 'res.country'
    sales_abroad_id = fields.One2many('res.sales.abroad', 'country_id')


class ir_attachment(models.Model):
    _inherit = 'ir.attachment'
    sales_abroad_id = fields.Many2one('res.sales.abroad', ondelete='restrict')

    def write(self, cr, uid, ids, vals, context=None):
        # Delete file from alternate directory
        attachments = self.browse(cr, uid, ids, context=context)
        directory = self.pool['ir.config_parameter'].get_param(cr, uid, 'sales_abroad.directory', '')
        for attach in attachments:
            if directory and attach.sales_abroad_id:
                file_name, file_ext = os.path.splitext(attach.datas_fname)
                file_dir = directory + '/' + _(attach.sales_abroad_id.country_id.name)

                file_full_path = file_dir + '/' + file_name + ' [' + str(attach.id) + ']' + file_ext
                if os.path.isfile(file_full_path):
                    os.unlink(file_full_path)

                if os.path.isdir(file_dir) and not os.listdir(file_dir):
                    os.rmdir(file_dir)

        res = super(ir_attachment, self).write(cr, uid, ids, vals, context=context)

        # Create new file in alternate directory
        attachments = self.browse(cr, uid, ids, context=context)
        source_dir = tools.config.filestore(cr.dbname)
        for attach in attachments:
            if directory and attach.sales_abroad_id:
                file_name, file_ext = os.path.splitext(attach.datas_fname)
                dest_dir = directory + '/' + _(attach.sales_abroad_id.country_id.name)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
                shutil.copyfile(
                    source_dir + '/' + attach.store_fname,
                    dest_dir + '/' + file_name + ' [' + str(attach.id) + ']' + file_ext
                )

        return res

    def unlink(self, cr, uid, ids, context=None):
        if isinstance(ids, (int, long)):
            ids = [ids]
        self.check(cr, uid, ids, 'unlink', context=context)

        attachments = [
            {
                'store_fname': a.store_fname,
                'datas_fname': a.datas_fname,
                'id': a.id,
                'country': a.sales_abroad_id.country_id.name if a.sales_abroad_id else ''

            }
                for a in self.browse(cr, uid, ids, context=context)
                    if a.store_fname
        ]

        res = super(ir_attachment, self).unlink(cr, uid, ids, context)

        # Alternate directory
        directory = self.pool['ir.config_parameter'].get_param(cr, uid, 'sales_abroad.directory', '')
        for a in attachments:
            self._file_delete(cr, uid, a['store_fname'])

            # Delete files from alternate directory
            if directory and a['country']:
                file_name, file_ext = os.path.splitext(a['datas_fname'])
                file_dir = directory + '/' + _(a['country'])

                file_full_path = file_dir + '/' + file_name + ' [' + str(a['id']) + ']' + file_ext
                if os.path.isfile(file_full_path):
                    os.unlink(file_full_path)

                if os.path.isdir(file_dir) and not os.listdir(file_dir):
                    os.rmdir(file_dir)

        return res

    def create(self, cr, uid, values, context=None):
        res = super(ir_attachment, self).create(cr, uid, values, context)

        # Create copy of file with original filename+id on alternate directory,
        # in his corresponding country folder
        attach = self.browse(cr, uid, res, context)
        source_dir = tools.config.filestore(cr.dbname)
        dest_dir = self.pool['ir.config_parameter'].get_param(cr, uid, 'sales_abroad.directory', '')
        if dest_dir and ('sales_abroad_id' in values):
            file_name, file_ext = os.path.splitext(attach.datas_fname)
            dest_dir = dest_dir + '/' + _(attach.sales_abroad_id.country_id.name)
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            shutil.copyfile(
                source_dir + '/' + attach.store_fname,
                dest_dir + '/' + file_name + ' [' + str(attach.id) + ']' + file_ext
            )

        return res


class stock_picking(models.Model):
    _inherit = 'stock.picking'
    docs_confirmed = fields.Boolean(default=False)
    docs_confirmed_check = fields.Boolean(compute='_docs_confirmed_check')

    def _docs_confirmed_check(self):
        for rec in self:
            rec.docs_confirmed = rec.docs_confirmed or\
                                 not bool(rec.partner_id.country_id.sales_abroad_id)
            rec.docs_confirmed_check = rec.docs_confirmed

    @api.multi
    def pre_transfer_checks(self):
        sp = self.browse(self.ids)
        country_id = sp.partner_id.country_id.id
        reference = sp.name
        return self.env['sales.abroad.confirm.docs'].wizard_view(country_id, reference)


class stock_move(models.Model):
    _inherit = 'stock.move'
    docs_confirmed = fields.Boolean(default=False)
    docs_confirmed_check = fields.Boolean(compute='_docs_confirmed_check')

    def _docs_confirmed_check(self):
        for rec in self:
            rec.docs_confirmed = rec.docs_confirmed or\
                                 rec.picking_id.docs_confirmed_check
            rec.docs_confirmed_check = rec.docs_confirmed

    @api.multi
    def pre_move_checks(self):
        sp = self.browse(self.ids).picking_id
        country_id = sp.partner_id.country_id.id
        reference = sp.name
        return self.env['sales.abroad.confirm.docs'].wizard_view(country_id, reference)


class stock_picking_wave(models.Model):
    _inherit = 'stock.picking.wave'
    docs_confirmed = fields.Boolean(default=False)
    docs_confirmed_check = fields.Boolean(compute='_docs_confirmed_check')

    def _docs_confirmed_check(self):
        for pw in self:
            pw.docs_confirmed = True
            for pl in pw.picking_ids:
                pw.docs_confirmed = pw.docs_confirmed and pl.docs_confirmed_check
            pw.docs_confirmed_check = pw.docs_confirmed

    @api.multi
    def pre_wave_checks(self):
        if not self.docs_confirmed_check:
            raise Warning(_("Please, check the documents of all picking lines."))