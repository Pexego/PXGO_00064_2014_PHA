# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus All Rights Reserved
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
#
##############################################################################

from openerp import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    has_sales_in_dimoni = fields.Boolean('¿Has sales in Dimoni?', default=False)

    @api.one
    @api.depends('commercial_partner_id',
                 'commercial_partner_id.sale_order_ids',
                 'commercial_partner_id.sale_order_ids.state',
                 'commercial_partner_id.child_ids',
                 'commercial_partner_id.child_ids.sale_order_ids',
                 'commercial_partner_id.child_ids.sale_order_ids.state')
    def _compute_prospect(self):
        res = super(ResPartner, self)._compute_prospect()
        return res and not self.has_sales_in_dimoni

