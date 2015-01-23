# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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

from openerp import models, api, _, exceptions
from openerp.osv import fields


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    _columns = {
        'state': fields.selection(
            [('draft', 'New'), ('cancel', 'Cancelled'),
             ('confirmed', 'Awaiting Raw Materials'),
             ('ready', 'Ready to Produce'),
             ('in_production', 'Production Started'), ('review', 'Review'), ('end_review', 'Review finished'),
             ('done', 'Done')],
            string='Status', readonly=True,
            track_visibility='onchange', copy=False,
            help="When the production order is created the status is set to 'Draft'.\n\
                If the order is confirmed the status is set to 'Waiting Goods'.\n\
                If any exceptions are there, the status is set to 'Picking Exception'.\n\
                If the stock is available then the status is set to 'Ready to Produce'.\n\
                When the production gets started then the status is set to 'In Production'.\n\
                When the production is over, the status is set to 'Done'."),
        'production_protocol_agreed': fields.boolean('Production protocol'),
        'production_ratio_agreed': fields.boolean('dosage and manufacturing ratios'),
        'production_isssue': fields.boolean('Production issue'),
        'production_review_by': fields.char('Revised by'),
        'production_review_notes': fields.text('Notes'),
        'production_review_date': fields.date('Revision Date'),
        'quality_material_agreed': fields.boolean('Starting material control'),
        'quality_process_agreed': fields.boolean('Process control'),
        'quality_analytical_agreed': fields.boolean('final product analytical control'),
        'quality_analytical_issue': fields.boolean('Analytical issue'),
        'quality_review_by': fields.char('Revised by'),
        'quality_review_notes': fields.text('Notes'),
        'quality_review_date': fields.date('Revision Date'),
        'tech_notes': fields.text('Notes'),
    }

    @api.one
    def action_production_review(self):
        self.state = 'review'

    @api.one
    def action_finish_review(self):
        self.state = 'end_review'


class MrpProductionWorkcenterLine(models.Model):

    _inherit = 'mrp.production.workcenter.line'

    @api.one
    def modify_production_order_state(self, action):
        """ Modifies production order state if work order state is changed.
        @param action: Action to perform.
        @return: Nothing
        """
        prod_obj = self.production_id
        if action == 'start':
            if prod_obj.state == 'confirmed':
                prod_obj.force_production()
                prod_obj.signal_workflow('button_produce')
            elif prod_obj.state == 'end_review':
                prod_obj.signal_workflow('button_produce')
            elif prod_obj.state == 'in_production':
                return
            else:
                raise exceptions.Warning(
                    _('Error!'),
                    _('Manufacturing order cannot be started in state "%s"!') %
                    (prod_obj.state,))
        else:
            open_count = self.search_count(
                [('production_id', '=', prod_obj.id), ('state', '!=', 'done')])
            flag = not bool(open_count)
            if flag:
                if prod_obj.move_lines or prod_obj.move_created_ids:
                    prod_obj.action_produce(prod_obj.product_qty,
                                            'consume_produce')
                prod_obj.signal_workflow('button_produce_done')
        return
