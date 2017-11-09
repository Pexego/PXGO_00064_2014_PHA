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
from openerp import models, fields, api, exceptions, _
from openerp.tools.safe_eval import safe_eval as eval
BOOL_STR_DICT = {
    True: 'APTO',
    False: 'NO APTO'

}


class StockLotAnalysis(models.Model):

    _name = 'stock.lot.analysis'

    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True)
    analysis_id = fields.Many2one('product.analysis', 'Analysis',
                                  required=True)
    result_str = fields.Char('Result')
    result_boolean = fields.Boolean('Result')
    result = fields.Char('Result', compute='_compute_result')
    expected_result = fields.Char('Expected result', compute='_compute_result')
    realized_by = fields.Char('Realized')
    proposed = fields.Boolean('Proposed')
    realized = fields.Boolean('Realized')
    show_in_certificate = fields.Boolean('Show in certificate')
    method = fields.Many2one('mrp.procedure', 'PNT')
    analysis_type = fields.Selection(
        (('boolean', 'Boolean'), ('expr', 'Expression'),
         ('free', 'Free text')))
    expected_result_boolean = fields.Boolean('Expected result')
    expected_result_expr = fields.Char('Expected result')
    expr_error = fields.Char(compute='_compute_passed')
    passed = fields.Boolean(compute='_compute_passed')

    @api.depends('result_str', 'result_boolean', 'analysis_type')
    def _compute_result(self):
        for analysis in self:
            expected_result = result = ''
            if analysis.analysis_type in ('free', 'expr'):
                result = analysis.result_str
                expected_result = analysis.expected_result_expr
            elif analysis.analysis_type == 'boolean':
                result = BOOL_STR_DICT[analysis.result_boolean]
                expected_result = BOOL_STR_DICT[analysis.expected_result_boolean]
            analysis.result = result
            analysis.expected_result = expected_result

    @api.depends('result_str', 'result_boolean', 'analysis_type',
                 'expected_result_boolean', 'expected_result_expr')
    def _compute_passed(self):
        for analysis in self:
            passed = False
            if analysis.analysis_type == 'boolean':
                if analysis.expected_result_boolean == analysis.result_boolean:
                    passed = True
            elif analysis.analysis_type == 'expr' and \
                    analysis.expected_result_expr and analysis.result_str:
                try:
                    x = float(analysis.result_str)
                    passed = eval(analysis.expected_result_expr,
                                  locals_dict={'x': x, 'X': x})
                except Exception, e:
                    analysis.expr_error = str(e)
            elif analysis.analysis_type == 'free':
                passed = True
            analysis.passed = passed


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    analysis_ids = fields.One2many('stock.lot.analysis', 'lot_id', 'Analysis')
    analysis_notes = fields.Text('Analysis notes')

    # Samples fields
    num_container_sample_proposed = fields.Integer(
        'Proposed number of containers to sample')
    num_sampling_proposed = fields.Integer('Proposed number of samples')

    num_container_sample_to_do = fields.Integer(
        'Number of containers to sample')
    num_sampling_to_do = fields.Integer('Number of samples')

    num_container_sample_realized = fields.Integer(
        'Number of containers sampled')
    num_sampling_realized = fields.Integer('Number of samples taked')
    sampling_notes = fields.Text('Sampling notes')
    sampling_date = fields.Date('Sampling date')
    sampling_realized = fields.Char('Sampling realized by')
    analysis_passed = fields.Boolean('Analysis passed',
                                     compute='_compute_analysis_passed')
    revised_by = fields.Char('Revised by')

    @api.depends('analysis_ids.passed')
    def _compute_analysis_passed(self):
        for lot in self:
            lot.analysis_passed = all([x.passed for x in lot.analysis_ids])

    @api.model
    def create(self, vals):
        lot = super(StockProductionLot, self).create(vals)
        if lot.product_id.analytic_certificate:
            for line in lot.product_id.analysis_ids:
                self.env['stock.lot.analysis'].create(
                    {'lot_id': lot.id,
                     'analysis_id': line.analysis_id.id,
                     'proposed': True,
                     'show_in_certificate': line.show_in_certificate,
                     'method': line.method.id,
                     'analysis_type': line.analysis_type,
                     'expected_result_boolean': line.expected_result_boolean,
                     'expected_result_expr': line.expected_result_expr
                     })
        return lot

    @api.multi
    def action_approve(self):
        for lot in self:
            if lot.product_id.analytic_certificate and not lot.analysis_passed:
                raise exceptions.Warning(
                    _('Analysis error'),
                    _('the consignment has not passed all analysis'))
        return super(StockProductionLot, self).action_approve()
