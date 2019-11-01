# -*- coding: utf-8 -*-
# © 2014 Comunitea
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class ProductLine(models.Model):
    _name = 'product.line'

    name = fields.Char('Name', size=64, required=True)


class ProductSubline(models.Model):
    _name = 'product.subline'

    name = fields.Char('Name', size=64, required=True)


class ProductPurchaseLine(models.Model):
    _name = 'product.purchase.line'

    name = fields.Char('Name', size=64, required=True)


class ProductPurchaseSubline(models.Model):
    _name = 'product.purchase.subline'

    name = fields.Char('Name', size=64, required=True)

class ProductPackingProduction(models.Model):
    _name = 'product.packing.production'

    name = fields.Char('Name', required=True)

class ProductPackingBase(models.Model):
    _name = 'product.packing.base'

    name = fields.Char('Name', required=True)
    number_of_objects = fields.Integer('Number of objects', required=True)

class product_form(models.Model):
    _name = 'product.form'

    name = fields.Char('Name', size=64)


class product_container(models.Model):
    _name = 'product.container'

    name = fields.Char('Name', size=64)


class product_quality_limits(models.Model):

    _name = 'product.quality.limits'

    name = fields.Many2one('product.template', required=True)
    active = fields.Boolean(default=True)

    # case_weight
    full_case_min_action_weight = fields.Float('Full case action min')
    full_case_max_action_weight = fields.Float('Full case action max')
    full_case_min_alert_weight = fields.Float('Full case alert min')
    full_case_max_alert_weight = fields.Float('Full case alert max')

    # Middleweight filter
    filter_av_min_action_weight = fields.Float('Average filter weight min action')
    filter_av_max_action_weight = fields.Float('Average filter weight max action')
    filter_av_min_alert_weight = fields.Float('Average filter weight min alert')
    filter_av_max_alert_weight = fields.Float('Average filter weight max alert')

    # filter weight
    filter_tare = fields.Float('Filter tare',
                               digits=dp.get_precision('Stock Weight'))
    filter_tare_str = fields.Char(compute='_filter_tare_str')
    filter_gross_weight = fields.Float('Filter gross weight',
                                       compute='_filter_gross_weight',
                                       digits=dp.get_precision('Stock Weight'))
    filter_gross_weight_str = fields.Char(compute='_filter_gross_weight')
    filter_min_action_weight = fields.Float('Filter weight min action')
    filter_max_action_weight = fields.Float('Filter weight max action')
    filter_min_alert_weight = fields.Float('Filter weight min alert')
    filter_max_alert_weight = fields.Float('Filter weight max alert')

    loc_samples = fields.Integer('Loc Samples')
    unit_weight_str = fields.Char('Unit weight',
                                  compute='_get_unit_weight_str')
    unit_weight = fields.Float('Unit weight', compute='_get_unit_weight',
                               store=True,
                               digits=dp.get_precision('Stock Weight'))
    analysis = fields.Integer('Analysis')
    tu1 = fields.Float('TU1')
    tu2 = fields.Float('TU2')
    to1 = fields.Float('TO1')
    to2 = fields.Float('TO2')

    _sql_constraints = [('name_unique', 'unique(name)',
                         'Unique product')]

    @api.depends('name.weight_net', 'name.qty')
    def _get_unit_weight(self):
        for spec in self:
            if spec.name.qty != 0:
                spec.unit_weight = spec.name.weight_net / spec.name.qty

    @api.depends('name.weight_net', 'name.qty')
    def _get_unit_weight_str(self):
        for spec in self:
            spec.unit_weight_str = '%s kg (%s g)' % \
                (spec.unit_weight, spec.unit_weight * 1000)

    @api.depends('filter_tare')
    def _filter_tare_str(self):
        for spec in self:
            spec.filter_tare_str = 'kg (%s g)' % (spec.filter_tare * 1000)

    @api.depends('filter_tare', 'name.weight_net', 'name.qty')
    def _filter_gross_weight(self):
        for spec in self:
            spec.filter_gross_weight = spec.unit_weight + spec.filter_tare
            spec.filter_gross_weight_str = 'kg (%s g)' % \
                                           (spec.filter_gross_weight * 1000)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cn_code = fields.Char('CN code', size=12)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cn_code = fields.Char('CN code', related='product_variant_ids.cn_code')

    objective = fields.Selection((('alimentation', 'Alimentation'),
                                  ('pharmacy', 'Pharmacy')), 'Objective')
    packing = fields.Float('Packing')
    packing_internal = fields.Float('Packing Internal')
    packing_production = fields.Many2one('product.packing.production',
                                         'Packing Production')
    packing_base = fields.Many2one('product.packing.base', 'Packing Base')
    country = fields.Many2one('res.country', 'Country')
    qty = fields.Float('Quantity')
    udm = fields.Many2one('product.uom', 'UdM')
    clothing = fields.Selection((('dressed', 'Dressed'),
                                 ('naked', 'Naked')), 'Clothing')
    customer = fields.Many2one('res.partner', 'Customer')
    line = fields.Many2one('product.line', 'Line')
    subline = fields.Many2one('product.subline', 'SubLine')
    purchase_line = fields.Many2one('product.purchase.line', 'Purchase Line')
    purchase_subline = fields.Many2one('product.purchase.subline',
                                       'Purchase SubLine')
    base_form_id = fields.Many2one('product.form', 'Base form')
    container_id = fields.Many2one('product.container', 'Container')
    quality_limits = fields.One2many(comodel_name='product.quality.limits',
                                     inverse_name='name',
                                     string='Process control')
    process_control = fields.Boolean('Process control')

    # For column search and sorting in views
    ean13 = fields.Char(string='EAN13 Barcode', store=True,
                        related='product_variant_ids.ean13')
    default_code = fields.Char(string='Internal Reference', store=True,
                               related='product_variant_ids.default_code')

    # This product is packed in a box of box_elements number
    box_elements = fields.Float('Number of elements in a box', required=False)

    @api.model
    def create(self, vals):
        tmpl = super(ProductTemplate, self).create(vals)
        if vals.get('cn_code', False):
            tmpl.cn_code = vals['cn_code']
        return tmpl


class ProductExtraCategory(models.Model):
    _name = 'product.extra.category'
    _description = 'Product Category'
    _inherit = 'product.category'
    _table = 'product_category'
