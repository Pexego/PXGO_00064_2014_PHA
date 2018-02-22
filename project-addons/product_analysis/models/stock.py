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
from openerp.tools.float_utils import float_round
from datetime import datetime

BOOL_STR_DICT = {
    True: 'APTO',
    False: 'NO APTO'

}


class StockLotAnalysis(models.Model):

    _name = 'stock.lot.analysis'

    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True,
                             ondelete='cascade')
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
         ('free', 'Free text')), default='free')
    expected_result_boolean = fields.Boolean('Expected result')
    expected_result_expr = fields.Char('Expected result')
    expr_error = fields.Char(compute='_compute_passed')
    passed = fields.Boolean(compute='_compute_passed')
    decimal_precision = fields.Float(digits=0, default=0.0001)
    raw_material_analysis = fields.Boolean()

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
                    x = float_round(
                        float(analysis.result_str),
                        precision_rounding=analysis.decimal_precision)
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
    analysis_passed = fields.Boolean('Analysis passed')
    revised_by = fields.Char('Revised by')
    used_lots = fields.Text(compute='_compute_used_lots')

    @api.multi
    def _compute_used_lots(self):
        for lot in self:
            quants = self.env['stock.quant'].search([('lot_id', '=', lot.id)])
            moves = self.env['stock.move']
            moves = quants.mapped('history_ids').filtered(
                lambda r: not r.parent_ids or r.production_id).mapped(
                'parent_ids')
            lots_str = [_('<table class="product_analysis_used_lots_table">'
                          '<thead><tr><th>Product</th><th>Ref F</th>'
                          '<th>Lot</th><th>Aprobation date</th><th>Lot state</th>'
                          '</tr></thead><tbody>')]
            for used_lot in moves.mapped('lot_ids'):
                lot_state_str = dict(
                    used_lot.fields_get(
                        ['state'])['state']['selection'])[used_lot.state]
                if used_lot.acceptance_date:
                    acceptance_date = datetime.strptime(
                        used_lot.acceptance_date, '%Y-%m-%d').strftime('%d/%m/%Y')
                else:
                    acceptance_date = ''
                lots_str.append(
                    u'<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td>'
                    '<td>{}</td></tr>'.format(
                        used_lot.product_id.name,
                        used_lot.product_id.default_code,
                        used_lot.name,
                        acceptance_date,
                        lot_state_str))

            if len(lots_str) != 1:
                lot.used_lots = ''.join(lots_str) + u'</tbody></table>'
            else:
                lot.used_lots = ''

    @api.model
    def create(self, vals):
        lot = super(StockProductionLot, self).create(vals)
        if lot.product_id.analytic_certificate:
            for line in lot.product_id.analysis_ids:
                self.env['stock.lot.analysis'].create(
                    {'lot_id': lot.id,
                     'analysis_id': line.analysis_id.id,
                     'proposed': True,
                     'raw_material_analysis': line.raw_material_analysis,
                     'show_in_certificate': line.show_in_certificate,
                     'method': line.method.id,
                     'analysis_type': line.analysis_type,
                     'expected_result_boolean': line.expected_result_boolean,
                     'expected_result_expr': line.expected_result_expr,
                     'decimal_precision': line.decimal_precision
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

    @api.multi
    def set_all_realized(self):
        self.mapped('analysis_ids').write({'realized': True})

    @api.multi
    def set_raw_material_analysis(self):
        for lot in self:
            quants = self.env['stock.quant'].search([('lot_id', '=', lot.id)])
            moves = self.env['stock.move']
            moves = quants.mapped('history_ids').filtered(
                lambda r: not r.parent_ids or r.production_id).mapped(
                'parent_ids')
            use_move = moves.filtered(
                lambda r: r.product_id.categ_id.analysis_sequence > 0).sorted(
                lambda r: r.product_id.categ_id.analysis_sequence)
            raw_lot = use_move and use_move[0].quant_ids and \
                use_move[0].quant_ids[0].lot_id or False
            for lot_analysis in self.analysis_ids.filtered('raw_material_analysis'):
                if not raw_lot:
                    raise exceptions.Warning(_(''), _(''))
                copy_lot = raw_lot.analysis_ids.filtered(
                    lambda r: r.analysis_id.id == lot_analysis.analysis_id.id)
                if copy_lot:
                    lot_analysis.unlink()
                    copy_lot.copy(default={'lot_id': lot.id,
                                           'raw_material_analysis': True})
