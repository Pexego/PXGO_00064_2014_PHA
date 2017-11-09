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
from openerp import models, fields


class product_analysis(models.Model):

    _name = 'product.analysis'

    name = fields.Char('Paramenter', translate=True, required=True)


class product_analysis_rel(models.Model):

    _name = 'product.analysis.rel'

    sequence = fields.Integer()
    product_id = fields.Many2one('product.template', 'Product')
    analysis_id = fields.Many2one('product.analysis', 'Analysis')
    show_in_certificate = fields.Boolean('Show in certificate')
    method = fields.Many2one('mrp.procedure', 'PNT')
    analysis_type = fields.Selection(
        (('boolean', 'Boolean'), ('expr', 'Expression'),
        ('free', 'Free text')))
    expected_result_boolean = fields.Boolean('Expected result')
    expected_result_expr = fields.Char('Expected result')
