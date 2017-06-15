# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class BomMemberOf(models.TransientModel):
    _name = 'bom.member.of'
    _inherits = {'product.product': 'product_id'}
    _description = 'Member of BoM'

    product_id = fields.Many2one(string='Product that is part of the BoM',
                                 comodel_name='product.product', required=True,
                                 ondelete='cascade', readonly=True)
    bom_id = fields.One2many(string='Bills of materials',
                             comodel_name='mrp.bom', compute='_dummy_function',
                             readonly=True)
    product_summary = fields.Char('Summary of product',
                                  related='product_id.name', readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(BomMemberOf, self).default_get(fields)
        ctx = self.env.context
        active_model = ctx.get('active_model', False)
        active_id = ctx.get('active_id', False)
        if active_model == 'product.stock.unsafety' and active_id:
            active_id = self.env['product.stock.unsafety'].\
                browse(active_id).product_id.id

        if active_id:
            bom_lines = self.env['mrp.bom.line'].search([
                ('product_id', '=', active_id),
                ('bom_id.active', '=', True),
                ('bom_id.product_id.active', '=', True)
            ])
            res['product_id'] = active_id
            res['bom_id'] = [bom_line.bom_id.id for bom_line in bom_lines]
        return res

    @api.multi
    def _dummy_function(self):
        # Dummy function to avoid unnecessary related field at mrp.bom
        return True
