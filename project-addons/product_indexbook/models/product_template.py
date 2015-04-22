# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
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
##############################################################################
#

from openerp import models, fields, api


class product_template(models.Model):
    _inherit = 'product.template'

    qc_has_pis = fields.Boolean(string='Has P.I.S.?', default=False, help="Has product identification sheet?")
    qc_species = fields.One2many(string='Species', comodel_name='qc.species.product.template.rel', inverse_name='product')
    qc_aspects = fields.Many2many(string='Aspects', comodel_name='qc.aspects')

    @api.multi
    def new_qc_pis_specimen(self):
        res = self.env['qc.pis'].new_specimen(self)
        return res