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


class stock_lot_analysis(models.Model):

    _name = 'stock.lot.analysis'

    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True)
    analysis_id = fields.Many2one('product.analysis', 'Analysis',
                                  required=True)
    result = fields.Char('Result')
    realized_by = fields.Char('Realized')
    proposed = fields.Boolean('Proposed')
    realized = fields.Boolean('Realized')


class stock_production_lot(models.Model):

    _inherit = 'stock.production.lot'

    analysis_ids = fields.One2many('stock.lot.analysis', 'lot_id', 'Analysis')
    analysis_notes = fields.Text('Analysis notes')

    # Samples fields
    num_container_sample_proposed = fields.Integer('Proposed number of containers to sample')
    num_sampling_proposed = fields.Integer('Proposed number of samples')

    num_container_sample_to_do = fields.Integer('Number of containers to sample')
    num_sampling_to_do = fields.Integer('Number of samples')

    num_container_sample_realized = fields.Integer('Number of containers sampled')
    num_sampling_realized = fields.Integer('Number of samples taked')
    sampling_notes = fields.Text('Sampling notes')
    sampling_date = fields.Date('Sampling date')
    sampling_realized = fields.Char('Sampling realized by')
    analysis_passed = fields.Boolean('Analysis passed',
                                     compute='_get_analysis_passed',
                                     store=True)
    revised_by = fields.Char('Revised by')

    @api.depends('analysis_ids.realized', 'analysis_ids.result')
    @api.multi
    def _get_analysis_passed(self):
        for lot in self:
            passed = True
            for analysis in lot.analysis_ids:
                if analysis.realized and not analysis.result:
                    passed = False
            lot.analysis_passed = passed

    @api.model
    def create(self, vals):
        lot = super(stock_production_lot, self).create(vals)
        if lot.product_id.analytic_certificate:
            for line in lot.product_id.analysis_ids:
                self.env['stock.lot.analysis'].create({'lot_id': lot.id,
                                                       'analysis_id': line.id,
                                                       'proposed': True})
        return lot

    @api.multi
    def action_approve(self):
        for lot in self:
            if lot.product_id.analytic_certificate and not lot.analysis_passed:
                raise exceptions.Warning(
                    _('Analysis error'),
                    _('the consignment has not passed all analysis'))
        return super(stock_production_lot, self).action_approve()
