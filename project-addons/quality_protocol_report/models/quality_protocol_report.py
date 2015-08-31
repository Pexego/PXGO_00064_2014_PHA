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

from openerp import models, fields, api, exceptions, _
import uuid


class QualityProtocolReport(models.Model):
    """Objeto usado para definir los diferentes documentos de protocolo"""

    _name = "quality.protocol.report"

    name = fields.Char("Name", required=True)
    type_id = fields.Many2one('protocol.type', 'Type', required=True)
    product_ids = fields.Many2many('product.product', 'product__protocol_rel',
                                   'protocol_id', 'product_id', 'Products')
    model_id = fields.Many2one("ir.model", "Model")
    report_line_ids = fields.Many2many('quality.protocol.report.line',
                                       'quality_protocols_lines_rel',
                                       'line_id', 'protocol_id', 'Sections')
    first_procedure_id = fields.Many2one('quality.procedure',
                                         'Primary procedure')
    second_procedure_id = fields.Many2one('quality.procedure',
                                          'Secondary procedure')
    product_form_id = fields.Many2one('product.form', 'Form')
    product_container_id = fields.Many2one('product.container', 'Container')

    @api.one
    @api.constrains('name', 'product_ids')
    def unique_name_product(self):
        for product in self.product_ids:
            if self.type_id.id in [x.type_id.id for x in product.protocol_ids
                                   if x.id != self.id]:
                raise exceptions.ValidationError(
                    _("The product %s has another protocol with the same type")
                    % product.name)


class protocol_type(models.Model):
    _name = 'protocol.type'

    name = fields.Char('Name', size=64)
    workcenter_ids = fields.One2many('mrp.workcenter', 'protocol_type_id',
                                     'Workcenter')
    is_hoard = fields.Boolean('Hoard')
    is_continuation = fields.Boolean('Continuation')


class QualityProtocolReportLine(models.Model):
    """
       Dentro de un documento de protodolo cada una  de sus secciones,
       se pueden asociar a vistas qweb o a surveys. Se ordenan por secuencia.
    """

    _name = "quality.protocol.report.line"
    _order = "sequence asc"

    view_id = fields.Many2one("ir.ui.view", 'Qweb View',
                              domain=[('type', '=', 'qweb')], copy=True)
    survey_id = fields.Many2one("survey.survey", "Survey")
    name = fields.Char("Name", required=True)
    sequence = fields.Integer("Sequence", default="1")
    report_ids = fields.Many2many('quality.protocol.report',
                                  'quality_protocols_lines_rel', 'protocol_id',
                                  'line_id', 'Reports')
    log_realization = fields.Boolean('Log realization')

    @api.multi
    def duplicate_line(self):
        report_id = self.env.context.get('report_id', False)
        new_line = self.copy()
        new_line.report_ids = [(6, 0, [report_id])]
        self.report_ids = [(3, report_id)]
        new_line.view_id = self.view_id.copy()
        model_data = self.env['ir.model.data'].search(
            [('model', '=', 'ir.ui.view'),
             ('res_id', '=', self.view_id.id)])
        new_model = model_data.copy({'res_id': new_line.view_id.id,
                                     'module': 'quality_protocol_report',
                                     'name':
                                     str(uuid.uuid4()).replace('-', ''),
                                     'noupdate': True})
        new_line.view_id.arch = new_line.view_id.arch.replace(
            self.view_id.xml_id, new_model.complete_name)
        return True
