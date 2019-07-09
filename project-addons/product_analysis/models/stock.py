# -*- coding: utf-8 -*-
# © 2014 Pexego
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions, _
from openerp.tools.safe_eval import safe_eval as eval
from openerp.tools.float_utils import float_round
from datetime import datetime


class StockLotAnalysis(models.Model):
    _name = 'stock.lot.analysis'
    _order = 'sequence'

    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True,
                             ondelete='cascade')
    analysis_id = fields.Many2one('product.analysis', 'Analysis',
                                  required=True)
    result_str = fields.Char('Result')
    result_boolean = fields.Boolean('Result')
    result_boolean_selection = fields.Selection([
        ('conformant', 'CONFORMANT'),
        ('qualify', 'QUALIFY'),
        ('presence', 'PRESENCE'),
        ('non_compliant', 'NON COMPLIANT'),
        ('not_qualify', 'NOT QUALIFY'),
        ('absence', 'ABSENCE'),
    ])
    result = fields.Char('Result', compute='_compute_result')
    expected_result = fields.Char('Expected result', compute='_compute_result')
    realized_by = fields.Char('Realized')
    proposed = fields.Boolean('Proposed')
    realized = fields.Boolean('Realized', default=True)
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
    criterion = fields.Selection([
        ('normal', ''),
        ('informative', 'INFORMATIVE')
    ], readonly=True)
    sequence = fields.Integer()

    @api.onchange('result_boolean_selection')
    def on_change_result_boolean_selection(self):
        self.result_boolean = self.result_boolean_selection in \
                              ('conformant', 'qualify', 'presence')

    @api.multi
#    @api.depends('result_str', 'result_boolean', 'analysis_type',
#                 'expected_result_expr', 'expected_result_boolean')
    def _compute_result(self):
        boolean_values = self._fields['result_boolean_selection'].\
            _description_selection(self.env)
        for analysis in self:
            expected_result = result = ''
            if analysis.analysis_type in ('free', 'expr'):
                result = analysis.result_str
                expected_result = analysis.expected_result_expr
            elif analysis.analysis_type == 'boolean':
                value = analysis.result_boolean_selection
                result = dict(boolean_values)[value] if value else False
                value = analysis.lot_id.product_id.analysis_ids.\
                    filtered(lambda r: r.analysis_id == analysis.analysis_id).\
                    boolean_selection
                expected_result = dict(boolean_values)[value] if value else False
            analysis.result = result
            analysis.expected_result = expected_result

    @api.depends('result_str', 'result_boolean', 'analysis_type',
                 'expected_result_boolean', 'expected_result_expr')
    @api.multi
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

    @api.multi
    def write(self, vals):
        if vals.get('result_boolean_selection') and not vals.get('result_boolean'):
            vals['result_boolean'] = vals.get('result_boolean_selection') in \
                                     ('conformant', 'qualify', 'presence')
        return super(StockLotAnalysis, self).write(vals)


class StockProductionLotStateChange(models.Model):
    _name = 'stock.production.lot.state.change'

    lot_id = fields.Many2one(comodel_name='stock.production.lot')
    state_old = fields.Selection((
        ('draft', 'New'),
        ('in_rev', 'Revision(Q)'),
        ('revised', 'Revised'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ))
    state_new = fields.Selection((
        ('draft', 'New'),
        ('in_rev', 'Revision(Q)'),
        ('revised', 'Revised'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected')
    ))


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    compliant_qualification = fields.Boolean(default=False)
    analysis_ids = fields.One2many('stock.lot.analysis', 'lot_id', 'Analysis')
    analysis_notes = fields.Text('Analysis notes')
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
    production_id = fields.Many2one(string='Manufacturing order',
                                    comodel_name='mrp.production',
                                    compute='_compute_used_lots',
                                    readonly=True)
    origin_type = fields.Selection([
        ('unspecified', 'Unspecified'),
        ('eu', 'EU product'),
        ('notEU', 'Not EU product'),
        ('eu_notEU', 'EU/not EU product'),
    ], default='unspecified')
    origin_country_id = fields.Many2one(comodel_name='res.country',
                                        string='Origin country')
    production_review_ids = fields.One2many(
        comodel_name='stock.lot.production.review',
        inverse_name='lot_id',
        string='Compliant with'
    )
    production_review_notes = fields.Text('Notes')
    production_review_done_by = fields.Char('Done by')
    production_review_date = fields.Date('Date')
    technical_direction_review_ids = fields.One2many(
        comodel_name='stock.lot.technical.direction.review',
        inverse_name='lot_id',
        string='Compliant with'
    )
    technical_direction_review_notes = fields.Text('Notes')
    technical_direction_review_done_by = fields.Char('Done by')
    technical_direction_review_date = fields.Date('Date')
    state_change_ids = fields.One2many(
        comodel_name='stock.production.lot.state.change',
        inverse_name='lot_id',
        readonly=True,
        string='State changes'
    )
    reception_notes = fields.Char()

    @api.onchange('origin_type')
    def onchange_origin_type(self):
        if self.origin_type == 'unspecified':
            self.origin_country_id = False

    @api.multi
    def _compute_used_lots(self):
        for lot in self:
            lots_str = [_('<table class="product_analysis_used_lots_table">'
                          '<thead><tr><th>Product</th><th>Ref F</th>'
                          '<th>Lot</th><th>Approbation date</th><th>Lot state</th>'
                          '</tr></thead><tbody>')]
            lot.production_id = self.env['mrp.production'].search([
                ('final_lot_id', '=', lot.id)])
            consumption_ids = lot.production_id.sudo().mapped('quality_consumption_ids')
            for consumption_id in consumption_ids:
                state = consumption_id.lot_id.state
                lot_state_str = dict(
                    consumption_id.lot_id.fields_get(['state'])['state']['selection']
                )[state]
                if consumption_id.lot_id.acceptance_date:
                    acceptance_date = datetime.strptime(
                        consumption_id.lot_id.acceptance_date, '%Y-%m-%d').\
                        strftime('%d/%m/%Y')
                else:
                    acceptance_date = ''
                lots_str.append(
                    u'<tr><td>{}</td><td>{}</td><td>{}</td><td>{}</td>'
                    '<td>{}</td></tr>'.format(
                        consumption_id.lot_id.product_id.name,
                        consumption_id.product_id.default_code,
                        consumption_id.lot_id.name,
                        acceptance_date,
                        lot_state_str))

            if len(lots_str) != 1:
                lot.used_lots = ''.join(lots_str) + u'</tbody></table>'
            else:
                lot.used_lots = ''

    @api.model
    def create(self, vals):
        vals['production_review_ids'] = []
        question_ids = self.env['stock.lot.production.review.question'].\
            search([])
        for question_id in question_ids:
            vals['production_review_ids'].append((0, 0, {
                'question_id': question_id.id,
                'sequence': question_id.sequence
            }))

        vals['technical_direction_review_ids'] = []
        question_ids = \
            self.env['stock.lot.technical.direction.review.question'].search([])
        for question_id in question_ids:
            vals['technical_direction_review_ids'].append((0, 0, {
                'question_id': question_id.id,
                'sequence': question_id.sequence
            }))

        vals['state_change_ids'] = [(0, 0, {
            'state_new': vals.get('state', 'draft')
        })]

        lot = super(StockProductionLot, self).create(vals)
        if lot.product_id.analytic_certificate:
            for line in lot.product_id.analysis_ids:
                self.env['stock.lot.analysis'].create({
                    'lot_id': lot.id,
                    'analysis_id': line.analysis_id.id,
                    'proposed': True,
                    'raw_material_analysis': line.raw_material_analysis,
                    'show_in_certificate': line.show_in_certificate,
                    'method': line.method.id,
                    'analysis_type': line.analysis_type,
                    'expected_result_boolean': line.expected_result_boolean,
                    'expected_result_expr': line.expected_result_expr,
                    'decimal_precision': line.decimal_precision,
                    'criterion': line.criterion,
                    'sequence': line.sequence
                })
        return lot

    @api.multi
    def write(self, vals):
        state = vals.get('state', False)
        if state:
            vals['state_change_ids'] = [(0, 0, {
                'state_old': self[0].state,
                'state_new': vals.get('state', 'draft')
            })]
        return super(StockProductionLot, self).write(vals)

    @api.multi
    def action_approve(self):
        for lot in self:
            if lot.product_id.analytic_certificate and not lot.analysis_passed:
                raise exceptions.Warning(
                    _('Analysis error'),
                    _('the consignment has not passed all analysis'))
        return super(StockProductionLot, self).action_approve()

    @api.one
    def copy_analysis_results(self, origin_lot_id):
        if self.env.context.get('full_analysis_copy'):
            analysis_ids = self.analysis_ids
        else:
            analysis_ids = self.analysis_ids.filtered('raw_material_analysis')

        for dest_analysis in analysis_ids:
            orig_analysis = origin_lot_id.analysis_ids.filtered(
                lambda r: r.analysis_id.id == dest_analysis.analysis_id.id)
            if orig_analysis:
                dest_analysis.unlink()
                orig_analysis.copy(default={'lot_id': self.id,
                                            'raw_material_analysis': True})

    @api.multi
    def set_raw_material_analysis(self):
        for lot in self:
            quants = self.env['stock.quant'].search([('lot_id', '=', lot.id)])
            moves = quants.mapped('history_ids').filtered(
                lambda r: not r.parent_ids or r.production_id).mapped(
                'parent_ids')
            use_move = moves.filtered(
                lambda r: r.product_id.categ_id.analysis_sequence > 0).sorted(
                lambda r: r.product_id.categ_id.analysis_sequence)
            raw_lot = use_move and use_move[0].quant_ids and \
                use_move[0].quant_ids[0].lot_id or False
            if not raw_lot or self.env.context.get('full_analysis_copy'):
                select_id = self.env['stock.production.lot.select'].create({
                    'dest_lot_id': self.id
                })
                wizard = self.env.ref(
                    'product_analysis.stock_production_lot_select_wizard')
                return {
                    'name': _('Lot from which the analysis parameters are to be copied'),
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'stock.production.lot.select',
                    'views': [(wizard.id, 'form')],
                    'view_id': wizard.id,
                    'target': 'new',
                    'res_id': select_id.id,
                }
            else:
                lot.copy_analysis_results(raw_lot)

    @api.multi
    def action_stock_lot_analysis_wizard(self):
        view = self.env.ref('product_analysis.stock_production_lot_analysis_wizard')
        return {
            'name': _('Edit questionnaire'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.production.lot',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }

    @api.multi
    def action_save_lot_analysis_wizard(self):
        self.analysis_ids._compute_passed()
        return self


class StockLotProductionReviewQuestion(models.Model):
    _name = 'stock.lot.production.review.question'
    _order = 'sequence'

    name = fields.Char(required=True)
    sequence = fields.Integer()
    active = fields.Boolean(default=True)


class StockLotProductionReview(models.Model):
    _name = 'stock.lot.production.review'
    _order = 'sequence'

    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True,
                             ondelete='cascade')
    question_id = fields.Many2one('stock.lot.production.review.question',
                                  'Question')
    result = fields.Selection([('yes', 'Yes'), ('no', 'No')])
    sequence = fields.Integer()


class StockLotTechnicalDirectionReviewQuestion(models.Model):
    _name = 'stock.lot.technical.direction.review.question'
    _order = 'sequence'

    name = fields.Char(required=True)
    sequence = fields.Integer()
    active = fields.Boolean(default=True)


class StockLotTechnicalDirectionReview(models.Model):
    _name = 'stock.lot.technical.direction.review'
    _order = 'sequence'

    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True,
                             ondelete='cascade')
    question_id = fields.Many2one('stock.lot.technical.direction.review.question',
                                  'Question')
    result = fields.Selection([('yes', 'Yes'), ('no', 'No'), ('na', 'N/A')])
    sequence = fields.Integer()


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    @api.multi
    def do_detailed_transfer_multi(self):
        super(StockTransferDetails, self).do_detailed_transfer()

        for lot_id in self.picking_id.mapped('pack_operation_ids.lot_id'):
            lot_id.compute_details_from_moves()
            if lot_id.production_id.state == 'in_production':
                report_name = 'product_analysis.' \
                              'lot_certification_and_partial_release_report'
            else:
                report_name = 'product_analysis.' \
                              'lot_certification_and_release_report'
            pdf = self.env['report'].get_pdf(lot_id, report_name)

        return {'type': 'ir.actions.act_window_close'}


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transfer_and_approve_available = fields.Boolean(
        compute='_transfer_and_approve_available')

    @api.multi
    def _transfer_and_approve_available(self):
        for picking_id in self:
            result = False
            if picking_id.state in ('assigned', 'partially_available') and \
                    picking_id.move_lines:
                quality_location_id = self.env.ref('__export__.stock_location_95')
                # True if move is in any child location of Quality Control,
                # any move reserved lot are revised and have analysis passed
                for move_id in picking_id.move_lines:
                    for lot_id in move_id.lot_ids:
                        result = result or (
                            (move_id.location_id.location_id ==
                             quality_location_id) and \
                            ((lot_id.state == u'revised') and \
                             lot_id.analysis_passed)
                        )
            picking_id.transfer_and_approve_available = result

    @api.multi
    def transfer_and_approve(self):
        self.ensure_one()
        aErrors = []
        quality_location_id = self.env.ref('__export__.stock_location_95')
        # True if move is in any child location of Quality Control,
        # any move reserved lot are revised and have analysis passed
        for move_id in self.move_lines:
            for lot_id in move_id.lot_ids:
                if (move_id.location_id.location_id != quality_location_id):
                    aErrors.append(move_id.product_id.name + ' - Lote: ' +
                                   lot_id.name + ' - Motivo: Ubicación no es '
                                                 'de Calidad')
                if (lot_id.state != 'revised') or not lot_id.analysis_passed:
                    aErrors.append(move_id.product_id.name + ' - Lote: ' +
                                   lot_id.name + ' - Motivo: Lote no está '
                                                 'revisado y/o análisis pasado')
        if aErrors:
            txtErrors = '';
            for error in aErrors:
                txtErrors += error + '<br/>'
            raise exceptions.Warning('Algunos movimientos no cumplen los '
                                     'requisitos', txtErrors)

        for move_id in self.move_lines:
            for lot_id in move_id.lot_ids:
                if not lot_id.production_id:
                    continue

                for tdr_id in lot_id.technical_direction_review_ids:
                    if tdr_id.question_id.id != 2:
                        tdr_id.result = 'yes'
                    else:
                        lowest_weight = 99999
                        lowest_weight_material_id = False
                        for bom_line_id in lot_id.production_id.bom_id.\
                                bom_line_ids:
                            weight = bom_line_id.product_id.categ_id.\
                                analysis_sequence
                            if weight < lowest_weight:
                                lowest_weight = weight
                                lowest_weight_material_id = bom_line_id.\
                                    product_id

                        if lowest_weight_material_id and \
                           lowest_weight_material_id.categ_id.\
                            analysis_sequence == 10 and \
                            lot_id.production_id.product_id.container_id.id in (25, 31):
                            tdr_id.result = 'na'
                        elif lowest_weight_material_id and \
                           lowest_weight_material_id.categ_id.\
                            analysis_sequence != 10:
                            tdr_id.result = 'na'
                        else:
                            tdr_id.result = 'yes'

                lot_id.technical_direction_review_done_by = self.env.user.\
                    partner_id.name
                lot_id.technical_direction_review_date = fields.Date.today()
                lot_id.action_approve()

        return self.with_context(transfer_and_approve = True).\
            do_enter_transfer_details()
