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
             ('qty_set', 'Final quantity set'),
             ('released', 'Released'),
             ('done', 'Done')],
            string='Status', readonly=True,
            track_visibility='onchange', copy=False,
            help="When the production order is created the status is set to 'Draft'.\n\
                If the order is confirmed the status is set to 'Waiting Goods'.\n\
                If any exceptions are there, the status is set to 'Picking Exception'.\n\
                If the stock is available then the status is set to 'Ready to Produce'.\n\
                When the production gets started then the status is set to 'In Production'.\n\
                When the production is over, the status is set to 'Done'."),
    }

    @api.multi
    def prod_act_final_qty(self):
        return self.write({'state': 'qty_set'})

    @api.multi
    def prod_act_release(self):
        return self.write({'state': 'released'})

    @api.model
    def _make_production_produce_line(self, production):
        prod_name = production.name
        procurement_group = self.env['procurement.group'].search(
            [('name', '=', prod_name)], limit=1)
        if not procurement_group:
            procurement_group = self.env['procurement.group'].create(
                {'name': prod_name})
        self = self.with_context(set_push_group=procurement_group.id)
        return super(MrpProduction, self)._make_production_produce_line(production)
