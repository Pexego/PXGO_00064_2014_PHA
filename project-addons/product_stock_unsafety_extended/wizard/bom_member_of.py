# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api


class BomMemberOf(models.TransientModel):
    _name = 'bom.member.of'
    _description = 'Member of BoM'

    product_id = fields.Many2one(string='Product that is part of the BoM',
                                 comodel_name='product.product', readonly=True)
    default_code = fields.Char(related='product_id.default_code')
    bom_id = fields.One2many(string='Bills of materials',
                             comodel_name='mrp.bom', compute='_get_related_bom',
                             readonly=True)

    @api.model
    def default_get(self, fields):
        res = super(BomMemberOf, self).default_get(fields)
        ctx = self.env.context
        if ctx.get('active_model') == 'product.product':
            res['product_id'] = ctx.get('active_id')
            bom_lines = self.env['mrp.bom.line'].search([('product_id', '=',
                                                          res['product_id'])])
            res['bom_id'] = [bom_line.bom_id.id for bom_line in bom_lines]
        return res

    @api.multi
    def _get_related_bom(self):
        return True


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    default_code = fields.Char(related='product_id.default_code')
