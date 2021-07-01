# -*- coding: utf-8 -*-
from openerp import models, fields, api, exceptions, _
from datetime import datetime
from pytz import timezone
from openerp.addons.web.http import request
import subprocess
import base64
import os


class EditableReport(models.Model):
    _name = 'editable.report'

    name = fields.Char('Name', required=True)
    view_id = fields.Many2one(comodel_name='ir.ui.view',
                              string='QWeb view',
                              domain="[('type', '=', 'qweb'),"
                                     " ('model', '!=', False),"
                                     " ('xml_id', '!=', False)]",
                              required=True)
    ref_form_ir_act_server = fields.Many2one(
        'ir.actions.server', 'Sidebar action', readonly=True,
        help='Sidebar action to make this template available on records '
             'of the related document model')
    ref_form_ir_value = fields.Many2one(
        'ir.values', 'Sidebar button', readonly=True,
        help='Sidebar button to open the sidebar action')
    ref_print_ir_act_server = fields.Many2one(
        'ir.actions.server', 'Sidebar action', readonly=True,
        help='Sidebar action to make this template available on records '
             'of the related document model')
    ref_print_ir_value = fields.Many2one(
        'ir.values', 'Sidebar button', readonly=True,
        help='Sidebar button to open the sidebar action')

    @api.multi
    def create_form_action(self):
        self.ensure_one()
        model_id = self.env['ir.model'].\
            search([('model', '=', self.view_id.model)])
        ref_form_ir_act_server = self.env['ir.actions.server'].sudo().create({
            'name': _('Edit: {}').format(self.view_id.name),
            'model_id': model_id.id,
            'state': 'code',
            'condition': True,
            'code': 'action = object.editable_report_form({})'.
                format(self.view_id.id)
        })
        ref_form_ir_act_server.create_action()
        self.write({
            'ref_form_ir_act_server': ref_form_ir_act_server.id,
            'ref_form_ir_value': ref_form_ir_act_server.menu_ir_values_id[0].id,
        })
        return True

    @api.multi
    def unlink_form_action(self):
        for obj in self:
            try:
                if obj.ref_form_ir_act_server:
                    obj.ref_form_ir_act_server.sudo().unlink()
                if obj.ref_form_ir_value:
                    obj.ref_form_ir_value.sudo().unlink()
            except:
                raise exceptions.Warning(
                    _('Warning'),
                    _('Deletion of the action record failed.'))
        return True

    @api.multi
    def create_print_action(self):
        self.ensure_one()
        model_id = self.env['ir.model']. \
            search([('model', '=', self.view_id.model)])
        ref_print_ir_act_server = self.env['ir.actions.server'].sudo().create({
            'name': _('Print: {}').format(self.view_id.name),
            'model_id': model_id.id,
            'state': 'code',
            'condition': True,
            'code': 'action = object.editable_report_print({})'.
                format(self.view_id.id)
        })
        ref_print_ir_act_server.create_action()
        self.write({
            'ref_print_ir_act_server': ref_print_ir_act_server.id,
            'ref_print_ir_value': ref_print_ir_act_server.menu_ir_values_id[0].id,
        })
        return True

    @api.multi
    def unlink_print_action(self):
        for obj in self:
            try:
                if obj.ref_print_ir_act_server:
                    obj.ref_print_ir_act_server.sudo().unlink()
                if obj.ref_print_ir_value:
                    obj.ref_print_ir_value.sudo().unlink()
            except:
                raise exceptions.Warning(
                    _('Warning'),
                    _('Deletion of the action record failed.'))
        return True

    @api.multi
    def unlink(self):
        self.unlink_form_action()
        self.unlink_print_action()
        return super(EditableReport, self).unlink()

    @api.one
    def copy(self, default=None):
        if default is None:
            default = {}
        default.update({
            'name': '',
            'ref_form_ir_act_server': False,
            'ref_form_ir_value': False,
            'ref_print_ir_act_server': False,
            'ref_print_ir_value': False
        })
        return super(EditableReport, self).copy(default)

    def current_datetime(self):
        return datetime.now(timezone(self.env.user.tz or 'Europe/Madrid'))

    @api.model
    def get_current_date(self):
        return self.current_datetime().strftime('%d/%m/%Y')

    @api.model
    def get_current_time(self):
        return self.current_datetime().strftime('%H:%M:%S')

    @api.model
    def get_current_datetime(self):
        return self.current_datetime().strftime('%d/%m/%Y %H:%M:%S')

    @api.multi
    def print_report(self, report_url):
        if not request:
            raise exceptions.Warning(_(''), _(''))
        session_id = request.session.sid
        config = self.env['ir.config_parameter']
        addons_url = config.get_param('addons_path')
        phantomjs_path = config.get_param('phantomjs_path')
        phantomjs_path = 'phantomjs' if not phantomjs_path else phantomjs_path
        phantom = [
            phantomjs_path,
            addons_url +
            '/editable_reports/static/src/js/phantom_url_to_pdf.js',
            session_id, '/tmp'] + [report_url]
        process = subprocess.Popen(phantom)
        process.communicate()

        fname = report_url.replace('/', '').replace(':', '')
        filepath = '/tmp/' + fname + '.pdf'
        fildecode = open(filepath, 'r')
        encode_data = fildecode.read()
        fildecode.close()

        active_model = self.env.context.get('active_model', False)
        active_id = self.env.context.get('active_id', False)
        if active_model and active_id:
            active_name = self.env[active_model].browse([active_id]).name
        else:
            dt = fields.Datetime.context_timestamp(self, datetime.now())
            active_name = dt.strftime('%d-%m-%Y_%Hh%M')
        filename =  str(active_name).lower() + '.pdf'
        attachment_data = {
            'name': filename,
            'datas_fname': filename,
            'datas': base64.b64encode(encode_data),
            'res_model': active_model,
            'res_id': self.env.context.get('active_id', False),
        }
        self.env['ir.attachment'].search(
            [('name', '=', attachment_data['name']),
             ('res_id', '=', attachment_data['res_id']),
             ('res_model', '=', attachment_data['res_model'])]).unlink()
        attachment = self.env['ir.attachment'].create(attachment_data)

        os.remove(filepath)

        return {
            'type': 'ir.actions.act_url',
            'target': 'self',
            'url': '/web/binary/saveas?model=ir.attachment&field=datas' +
                   '&filename_field=name&id=%s' % (attachment.id),
        }
