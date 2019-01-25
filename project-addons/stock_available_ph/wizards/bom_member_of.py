# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class BomMemberOf(models.TransientModel):
    _name = 'bom.member.of'
    _inherits = {'product.product': 'product_id'}
    _description = 'Member of BoM'

    product_id = fields.Many2one(string='Product that is part of BoM',
                                 comodel_name='product.product', required=True,
                                 ondelete='cascade', readonly=True)
    bom_ids = fields.One2many(string='Bills of materials',
                              comodel_name='mrp.bom', readonly=True,
                              compute='_dummy_function')
    indirect_bom_ids = fields.One2many(string='Indirect bills of materials',
                                       comodel_name='mrp.bom', readonly=True,
                                       compute = '_dummy_function')
    product_summary = fields.Char('Summary of product',
                                  related='product_id.name', readonly=True)

    @api.model
    def default_get(self, fields):
        ctx = self.env.context
        active_model = ctx.get('active_model', False)
        active_id = ctx.get('active_id', False)
        if active_model and active_id:
            obj_id = self.env[active_model].browse(active_id)
            if active_model == 'product.product':
                active_id = obj_id.id
            else:
                active_id = obj_id.product_id.id

        res = super(BomMemberOf, self).default_get(fields)

        if active_id:
            def get_indirect_bom_ids(product_id):
                ind_bom_line_ids = self.env['mrp.bom.line'].search([
                    ('product_id', '=', product_id),
                    ('bom_id.active', '=', True),
                    ('bom_id.product_id.active', '=', True),
                    ('bom_id.sequence', '<', 100)
                ])
                for ind_bom_line_id in ind_bom_line_ids:
                    if ind_bom_line_id.bom_id.id not in indirect_bom_ids:
                        indirect_bom_ids.add(ind_bom_line_id.bom_id.id)
                        get_indirect_bom_ids(ind_bom_line_id.bom_id.
                                             product_id.id)

            bom_ids = set()
            indirect_bom_ids = set()

            bom_line_ids = self.env['mrp.bom.line'].search([
                ('product_id', '=', active_id),
                ('bom_id.active', '=', True),
                ('bom_id.product_id.active', '=', True),
                ('bom_id.sequence', '<', 100)
            ])
            for bom_line_id in bom_line_ids:
                bom_ids.add(bom_line_id.bom_id.id)
                get_indirect_bom_ids(bom_line_id.bom_id.product_id.id)

            res['bom_ids'] = list(bom_ids)
            res['indirect_bom_ids'] = list(indirect_bom_ids - bom_ids)
            res['product_id'] = active_id
        return res

    @api.multi
    def _dummy_function(self):
        # Dummy function to avoid unnecessary related field at mrp.bom
        return True
