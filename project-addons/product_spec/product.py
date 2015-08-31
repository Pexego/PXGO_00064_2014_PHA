# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Omar Castiñeira Saavedra <omar@pexego.es>$
#    $Marta Vázquez Rodríguez <marta@pexego.es>$
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
from openerp import models, fields, api


class ProductLine(models.Model):
    _name = 'product.line'

    name = fields.Char('Name', size=64, required=True)


class ProductSubline(models.Model):
    _name = 'product.subline'

    name = fields.Char('Name', size=64, required=True)


class ProductPacking(models.Model):
    _name = 'product.packing'

    name = fields.Char('Name', required=True)


class ProductPackingInternal(models.Model):
    _name = 'product.packing.internal'

    name = fields.Char('Name', required=True)

class ProductPackingProduction(models.Model):
    _name = 'product.packing.production'

    name = fields.Char('Name', required=True)

class ProductPackingBase(models.Model):
    _name = 'product.packing.base'

    name = fields.Char('Name', required=True)

class product_form(models.Model):
    _name = 'product.form'

    name = fields.Char('Name', size=64)


class product_container(models.Model):
    _name = 'product.container'

    name = fields.Char('Name', size=64)


class product_quality_limits(models.Model):

    _name = "product.quality.limits"

    name = fields.Char('Name', size=64, required=True)
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
    filter_min_action_weight = fields.Float('Filter weight min action')
    filter_max_action_weight = fields.Float('Filter weight max action')
    filter_min_alert_weight = fields.Float('Filter weight min alert')
    filter_max_alert_weight = fields.Float('Filter weight max alert')

    loc_samples = fields.Integer('Loc Samples')
    unit_weight = fields.Float('Unit weight')
    analysis = fields.Integer('Analysis')


class ProductProduct(models.Model):
    _inherit = 'product.product'

    cn_code = fields.Char('CN code', size=12)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    cn_code = fields.Char('CN code', related='product_variant_ids.cn_code')

    objective = fields.Selection((('alimentation', 'Alimentation'),
                                  ('pharmacy', 'Pharmacy')), 'Objective')
    packing = fields.Many2one('product.packing', 'Packing')
    packing_internal = fields.Many2one('product.packing.internal', 'Packing Internal')
    packing_production = fields.Many2one('product.packing.production', 'Packing Production')
    packing_base = fields.Many2one('product.packing.base', 'Packing Base')
    country = fields.Many2one('res.country', 'Country')
    qty = fields.Float('Quantity')
    udm = fields.Many2one('product.uom', 'UdM')
    clothing = fields.Selection((('dressed', 'Dressed'),
                                 ('naked', 'Naked')), 'Clothing')
    customer = fields.Many2one('res.partner', 'Customer')
    line = fields.Many2one('product.line', 'Line')
    subline = fields.Many2one('product.subline', 'SubLine')
    base_form_id = fields.Many2one('product.form', 'Base form')
    container_id = fields.Many2one('product.container', 'Container')
    quality_limits = fields.Many2one('product.quality.limits', 'Process control')
    process_control = fields.Boolean('Process control')

    # For column search and sorting in views
    ean13 = fields.Char(string='EAN13 Barcode', store=True, related='product_variant_ids.ean13')
    default_code = fields.Char(string='Internal Reference', store=True, related='product_variant_ids.default_code')

    @api.model
    def create(self, vals):
        tmpl = super(ProductTemplate, self).create(vals)
        if vals.get('cn_code'):
            tmpl.cn_code = vals['cn_code']
        return tmpl

class product_extra_category(models.Model):
    _name = 'product.extra.category'
    _description = "Product Category"
    _inherit = 'product.category'
    _table = 'product_category'