# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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

from openerp import models, api


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    @api.model
    def reset_product_sequences(self):
        for product in self.env['product.product'].search([('sequence_id',
                                                            '!=', False)]):
            pre_suffix = str(product.sequence_id.prefix) + \
                str(product.sequence_id.suffix)
            year_keys = ['%(year)s', '%(y)s', '%(year_last)s']
            if filter(lambda x: x in pre_suffix, year_keys):
                product.sequence_id.number_next_actual = 1
        return True
