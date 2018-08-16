# -*- coding: utf-8 -*-
# © 2014 Pexego
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ProductAnalysis(models.Model):
    _name = 'product.analysis'

    name = fields.Char('Parameter', translate=True, required=True)


class ProductAnalysisRel(models.Model):
    _name = 'product.analysis.rel'
    _order = 'sequence'
    _rec_name = 'product_id'

    sequence = fields.Integer()
    product_id = fields.Many2one('product.template', 'Product')
    analysis_id = fields.Many2one('product.analysis', 'Analysis')
    show_in_certificate = fields.Boolean()
    method = fields.Many2one('mrp.procedure', 'PNT')
    analysis_type = fields.Selection(
        (('boolean', 'Boolean'), ('expr', 'Expression'),
         ('free', 'Free text')))
    expected_result_boolean = fields.Boolean('Expected result')
    expected_result_expr = fields.Char('Expected result')
    raw_material_analysis = fields.Boolean()
    decimal_precision = fields.Float(digits=0, default=0.0001)
    boolean_selection = fields.Selection([
        ('conformant', 'CONFORMANT'),
        ('qualify', 'QUALIFY'),
        ('presence', 'PRESENCE'),
        ('non_compliant', 'NON COMPLIANT'),
        ('not_qualify', 'NOT QUALIFY'),
        ('absence', 'ABSENCE'),
    ])
    criterion = fields.Selection([
        ('normal', ''),
        ('informative', 'INFORMATIVE')
    ], default='normal')

    @api.onchange('analysis_type')
    def on_change_analysis_type(self):
        if self.analysis_type == 'boolean':
            self.expected_result_expr = False
        elif self.analysis_type == 'expr':
            self.boolean_selection = False
        else:
            self.boolean_selection = False
            self.expected_result_expr = False

    @api.onchange('boolean_selection')
    def on_change_boolean_selection(self):
        self.expected_result_boolean = self.boolean_selection in \
                                       ('conformant', 'qualify', 'presence')

    @api.model
    def create(self, vals):
        if not vals.get('product_id'):
            vals['product_id'] = self.env.context.get('active_id')
        return super(ProductAnalysisRel, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('analysis_type') != 'boolean':
            vals['boolean_selection'] = False
        else:
            vals['expected_result_expr'] = False
        return super(ProductAnalysisRel, self).write(vals)
