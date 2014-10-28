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

from openerp import models, fields, api


class QualityProtocolReport(models.Model):
    """Objeto usado para definir los diferentes documentos de protocolo"""

    _name = "quality.protocol.report"

    name = fields.Char("Name", required=True)
    type_id = fields.Many2one('protocol.type', 'Type', required=True)
    product_ids = fields.One2many('product.product', string='Products',
                                  compute='_get_product_ids')
    model_id = fields.Many2one("ir.model", "Model")
    report_line_ids = fields.One2many("quality.protocol.report.line",
                                      "report_id", "Sections")
    protocol_ids = fields.One2many('product.protocol', 'protocol_id',
                                   string="Protocols")
    first_procedure_id = fields.Many2one('quality.procedure',
                                         'Primary procedure')
    second_procedure_id = fields.Many2one('quality.procedure',
                                          'Secondary procedure')

    @api.depends('protocol_ids.product_ids')
    def _get_product_ids(self):
        self.product_ids = self.mapped('protocol_ids.product_ids').sorted()


class protocol_type(models.Model):
    _name = 'protocol.type'
    name = fields.Char('Name', size=64)


class QualityProtocolReportLine(models.Model):
    """Dentro de un documento de protodolo cada una  de sus secciones,
se pueden asociar a vistas qweb o a surveys. Se ordenan por secuencia."""

    _name = "quality.protocol.report.line"
    _order = "sequence asc"

    view_id = fields.Many2one("ir.ui.view", 'Qweb View',
                              domain=[('type', '=', 'qweb')])
    survey_id = fields.Many2one("survey.survey", "Survey")
    name = fields.Char("Name", required=True)
    sequence = fields.Integer("Sequence", default="1")
    report_id = fields.Many2one("quality.protocol.report", "Report")
