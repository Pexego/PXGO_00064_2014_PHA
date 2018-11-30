# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp
from openerp.workflow.service import WorkflowService


class MrpProductionConfirm(models.TransientModel):
    _name = 'mrp.production.confirm'

    production_id = fields.Many2one(comodel_name='mrp.production')
    product = fields.Char()
    bom = fields.Char()
    routing = fields.Char()
    final_lot = fields.Char()
    next_lot = fields.Char()
    quantity = fields.Float(digits=dp.get_precision('Product Unit of Measure'))
    quantity_text = fields.Char(string='Quantity', compute='_quantity_text')
    uom_id = fields.Many2one(comodel_name='product.uom')

    @api.one
    @api.depends('quantity')
    def _quantity_text(self):
        self.quantity_text = '{:g}'.format(self.quantity)

    @api.multi
    def action_confirm_production(self):
        self.production_id.action_confirm_production()

    @api.multi
    def action_cancel_production(self):
        # Reset the workflow
        wkf = WorkflowService.new(
            self.env.cr,
            self.env.user.id,
            'mrp.production',
            self.production_id.id
        )
        wkf.delete()
        wkf.create()