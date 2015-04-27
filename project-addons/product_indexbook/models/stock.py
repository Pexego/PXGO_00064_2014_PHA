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

class stock_location(models.Model):
    _inherit = 'stock.location'

    qc_location = fields.Boolean(string='Is a quarantine location?', default=False)


class stock_quant(models.Model):
    _inherit = 'stock.quant'

    @api.model
    def qc_check_if_need_pis(self, vals):
        # Check if destination location are affected by quality control, product has P.I.S. and move has lot assigned
        # If true, create new product identification sheet entry
        location = self.env['stock.location'].browse([vals['location_id']])
        product = self.env['product.template'].browse([vals['product_id']])
        if location.qc_location and product.qc_has_pis and vals['lot_id']:
            self.env['qc.pis'].create({'lot': vals['lot_id'], 'reference': vals['product_id']})


    @api.model
    def create(self, vals):
        self.qc_check_if_need_pis(vals)
        return super(stock_quant, self).create(vals)
