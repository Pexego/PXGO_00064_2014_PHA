# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
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


class ProductTemplate(models.Model):

    _inherit = 'product.template'

    analysis_ids = fields.One2many('product.analysis.rel', 'product_id',
                                   'Analysis')
    analytic_certificate = fields.Boolean()
    analysis_count = fields.Integer(compute='_compute_analysis_count')

    @api.one
    @api.depends('analysis_ids')
    def _compute_analysis_count(self):
        self.analysis_count = len(self.analysis_ids)

    @api.multi
    def action_view_analysis(self):
        result = self.env.ref(
            'product_analysis.product_analysis_rel_action').read()[0]
        result['domain'] = "[('id','in',[" + \
            ','.join(map(str, self.mapped('analysis_ids.id'))) + "])]"
        result['context'] = "{}"
        return result


class ProductCategory(models.Model):

    _inherit = 'product.category'

    analysis_sequence = fields.Integer()
