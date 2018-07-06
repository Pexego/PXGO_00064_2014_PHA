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


class ProductProtocolLink(models.Model):

    _name = 'product.protocol.link'

    protocol = fields.Many2one('quality.protocol.report')
    product = fields.Many2one('product.product', required=True)
    product_route_ids = fields.Many2many(related='product.routing_ids')
    prod_tmpl_id = fields.Many2one('product.template', related='product.product_tmpl_id')
    bom = fields.Many2one('mrp.bom')
    route = fields.Many2one('mrp.routing')


class QualityProtocolReportLineRel(models.Model):

    _name = 'quality.protocol.report.lines.rel'
    _order = "sequence asc"

    protocol_id = fields.Many2one('quality.protocol.report', 'Protocol')
    line_id = fields.Many2one('quality.protocol.report.line', 'Line')
    sequence = fields.Integer(default=1)

    _sql_constraints = [
        ('report_line_rel_unique', 'unique (protocol_id, line_id)', '')
    ]


class QualityProtocolReport(models.Model):
    """Objeto usado para definir los diferentes documentos de protocolo"""

    _name = "quality.protocol.report"

    name = fields.Char("Name", required=True)
    type_id = fields.Many2one('protocol.type', 'Type', required=True)
    product_ids = fields.One2many('product.protocol.link', 'protocol', 'Products')
    model_id = fields.Many2one("ir.model", "Model")
    report_lines = fields.One2many('quality.protocol.report.lines.rel', 'protocol_id', 'Sections')
    report_line_ids = fields.Many2many('quality.protocol.report.line', compute='_compute_line_ids', string='Sections')
    product_form_id = fields.Many2one('product.form', 'Form')
    product_container_id = fields.Many2one('product.container', 'Container')

    def _compute_line_ids(self):
        for report in self:
            report.report_line_ids = report.mapped('report_lines.line_id')


class ProtocolType(models.Model):
    _name = 'protocol.type'

    name = fields.Char('Name', size=64)
    workcenter_ids = fields.One2many('mrp.workcenter', 'protocol_type_id',
                                     'Workcenter')
    is_hoard = fields.Boolean('Hoard')
    is_continuation = fields.Boolean('Continuation')
    group_print = fields.Boolean('Group print')
    weight = fields.Integer(default=0)
    active = fields.Boolean(default=True)


class QualityProtocolReportLine(models.Model):
    """
       Dentro de un documento de protodolo cada una  de sus secciones,
       se pueden asociar a vistas qweb o a surveys. Se ordenan por secuencia.
    """

    _name = "quality.protocol.report.line"

    view_id = fields.Many2one("ir.ui.view", 'Qweb View',
                              domain=[('type', '=', 'qweb')], copy=True)
    survey_id = fields.Many2one("survey.survey", "Survey")
    name = fields.Char("Name", required=True)
    # sequence = fields.Integer("Sequence", default="1")
    # show_sequence = fields.Integer("Sequence to show", default="1")
    report_ids = fields.One2many('quality.protocol.report.lines.rel', 'line_id', 'Reports')
    report_reference_ids = fields.One2many(
        comodel_name='quality.protocol.report.reference',
        inverse_name='report_line_id',
        string='Quality protocol reports references')
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


class QualityProtocolReportReference(models.Model):
    _name = 'quality.protocol.report.reference'
    _rec_name = 'model_id'
    _order = 'model_id'

    report_line_id = fields.Many2one(comodel_name='quality.protocol.report.line',
                                     string='Quality protocol report section')
    model_id = fields.Many2one(comodel_name='ir.model', string='Model')
    data_reference = fields.Char(string='Data reference')
    active = fields.Boolean(default=True)
