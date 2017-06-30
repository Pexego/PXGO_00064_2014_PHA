# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, _, exceptions
from openerp.osv import fields
from datetime import date

class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    _columns = {
        'state': fields.selection(
            [('draft', 'New'), ('cancel', 'Cancelled'),
             ('confirmed', 'Awaiting Raw Materials'),
             ('ready', 'Ready'),
             ('in_production', 'In production'),
             ('in_review', 'Review'),
             ('wait_release', 'Waiting release'),
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
        'prod_review_ok': fields.boolean('production reviewed'),
        'qual_review_ok': fields.boolean('production reviewed'),
    }

    def copy(self, cr, uid, id, default={}, context=None):
        default['prod_review_ok'] = False
        default['qual_review_ok'] = False
        default['tech_notes'] = False
        default['quality_review_date'] = False
        default['quality_review_notes'] = False
        default['quality_review_by'] = False
        default['quality_analytical_issue'] = False
        default['quality_analytical_agreed'] = False
        default['quality_material_agreed'] = False
        default['production_review_date'] = False
        default['production_review_notes'] = False
        default['production_review_by'] = False
        default['production_isssue'] = False
        default['production_ratio_agreed'] = False
        default['production_protocol_agreed'] = False
        return super(MrpProduction, self).copy(cr, uid, id, default, context)

    @api.multi
    def action_finish_prod(self):
        self.write({'state': 'wait_release'})

    @api.multi
    def action_production_review(self):
        self.write({'state': 'in_review'})

    @api.multi
    def action_produce_start(self):
        self.signal_workflow('button_produce')

    @api.one
    def production_review(self):
        self.write({'production_review_by': self.env.user.partner_id.name,
                    'production_review_date': date.today(),
                    'prod_review_ok': True})

    @api.one
    def quality_review(self):
        self.write({'quality_review_by': self.env.user.partner_id.name,
                    'quality_review_date': date.today(),
                    'qual_review_ok': True})

    @api.multi
    def test_production_done_not_review(self):
        res = self.test_production_done()
        for production in self:
            if production.product_id.categ_id.needs_mrp_review:
                res = False
        return res

    @api.multi
    def test_production_done_review(self):
        res = self.test_production_done()
        for production in self:
            if not production.product_id.categ_id.needs_mrp_review:
                res = False
        return res


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
            elif prod_obj.state == 'ready':
                prod_obj.signal_workflow('button_produce')
            elif prod_obj.state in ('in_review', 'wait_release'):
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


class mrp_product_produce(models.TransientModel):
    _inherit = 'mrp.product.produce'

    @api.multi
    def do_produce(self):
        if self.mode != 'only_produce':
            production_id = self.env.context.get('active_id', False)
            assert production_id, "Production Id should be specified in context as a Active ID."
            self.env['mrp.production'].browse(production_id).signal_workflow('end_production')
        return super(mrp_product_produce,self).do_produce()