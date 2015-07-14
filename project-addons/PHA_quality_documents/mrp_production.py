# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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


class MrpProductionWorkcenterLine(models.Model):

    _inherit = 'mrp.production.workcenter.line'

    adjustsments_ids = fields.One2many('mrp.production.adjustments',
                                       'production_id', 'Adjustments')
    control_ids = fields.One2many('mrp.production.control',
                                  'Workcenter_line_id', 'Controls')
    on_time_machine = fields.Datetime('On time machine')
    wender_temp_ids = fields.One2many('mrp.wender.temp', 'workcenter_line_id',
                                      'Wender temps')
    mrp_speed = fields.Float('Mrp speed')
    adjustement_lever = fields.Float('adjustment lever')
    fallen_scale = fields.Float('Fallen scale')
    slow_funnel = fields.Float('slow funnel')
    fast_funnel = fields.Float('fast funnel')
    printed_configured_by = fields.Char('Configured printer by', size=64)
    confirmed_printer = fields.Char('Confirmed printer', size=64)
    printed_lot = fields.Char('Printed lot', size=64)
    printed_date = fields.Datetime('Printed date')
    print_comprobations = fields.One2many('mrp.print.comprobations',
                                          'wkcenter_line_id',
                                          'Print comprobations')
    mrp_start_date = fields.Datetime('Start production')
    final_count = fields.Integer('Final counter')
    continue_next_day = fields.Boolean('Continue production next day')
    fab_issue = fields.Boolean('Production issue')
    issue_ref = fields.Char('Issue ref', size=64)
    total_produced = fields.Float('Total produced')
    observations = fields.Text('Observations')
    wrap_comprobations = fields.One2many('mrp.wrap.comprobations',
                                         'wkcenter_line_id',
                                         'Print comprobations')
    print_comprobations_sec = fields.One2many('mrp.print.comprobations.sec',
                                              'wkcenter_line_id',
                                              'Print comprobations')

    coffin_works = fields.One2many('mrp.coffin.works', 'wkcenter_line_id',
                                   'Coffin works')
    qty_produced = fields.One2many('mrp.qty.produced', 'wkcenter_line_id',
                                   'Qty produced')
    lot_tag_ok = fields.Boolean('Validated lot number of tags')
    acond_issue = fields.Boolean('issue')
    acond_issue_ref = fields.Char('Issue ref', size=64)
    accond_total_produced = fields.Float('Total produced')
    accond_theorical_produced = fields.Float('Theorical produced')
    prod_ratio = fields.Float('Production ratio')
    acond_observations = fields.Text('Observations')


class MrpProductionAdjustments(models.Model):

    _name = "mrp.production.adjustments"

    name = fields.Char("Description", required=True)
    production_id = fields.Many2one("mrp.production.workcenter.line",
                                    "Production")
    start_date = fields.Datetime("Start date")
    reanudation_date = fields.Datetime("Reanudation date")
    initials = fields.Char("Initials")


class mrpQtyProduced(models.Model):

    _name = 'mrp.qty.produced'

    date = fields.Date('Date')
    coffins = fields.Integer('Coffins')
    boxes = fields.Integer('Boxes')
    case = fields.Integer('Case')
    initials = fields.Char('Initials')
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')


class MrpWrapComprobations(models.Model):

    _name = 'mrp.wrap.comprobations'

    date = fields.Datetime('Date')
    correct = fields.Boolean('Print correct')
    quality_sample = fields.Char('Quality sample', size=64)
    initials = fields.Char('Initials', size=12)
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')
    type = fields.Selection(
        (('wrap', 'Wrap'), ('box', 'Box')),
        'Type')

    @api.model
    def create(self, vals):
        type = self.env.context.get('type', False)
        if 'type' not in vals.keys() and type:
            vals['type'] = type
        return super(MrpWrapComprobations, self).create(vals)


class MrpPrintComprobationsCoffin(models.Model):

    _name = 'mrp.coffin.works'

    init_date = fields.Datetime('Init date')
    end_date = fields.Datetime('End date')
    initials = fields.Char('Initials', size=12)
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')


class MrpPrintComprobations(models.Model):

    _name = 'mrp.print.comprobations'

    date = fields.Datetime('Date')
    correct = fields.Boolean('Print correct')
    initials = fields.Char('Initials', size=12)
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')


class MrpPrintComprobationsSec(models.Model):

    _name = 'mrp.print.comprobations.sec'

    date = fields.Date('Date')
    lot_correct = fields.Boolean('Lot correct')
    date_correct = fields.Boolean('Date correct')
    initials = fields.Char('Initials', size=12)
    wkcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                       'Workcenter line')


class MrpWenderTemp(models.Model):

    _name = 'mrp.wender.temp'

    sequence = fields.Integer('Wender nº')
    temperature = fields.Float('Temperature')
    workcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                         'Workcenter line')


class MrpProductionControl(models.Model):

    _name = 'mrp.production.control'

    date = fields.Datetime('Hour')
    bag_maked = fields.Boolean('Maked')
    label = fields.Boolean('label')
    wrapped = fields.Boolean('wrapped')
    full_weight = fields.Float('Full')
    empty_weight = fields.Float('Empty')
    first = fields.Float('First production')
    middle = fields.Float('Middle production')
    last = fields.Float('Final production')
    initials = fields.Char("Initials")
    Workcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                         'Workcenter line')
