# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
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

from openerp import models, fields


class SaleReport(models.Model):
    _inherit = 'sale.report'

    shipping_country_id = fields.Many2one('res.country', 'Shipping country')

    def _select(self):
        select_str = super(SaleReport, self)._select()
        return select_str + ', spa.country_id as shipping_country_id '

    def _from(self):
        from_str = super(SaleReport, self)._from()
        return from_str + """
            left join res_partner spa on spa.id = s.partner_shipping_id
                and spa.company_id = s.company_id
            """

    def _group_by(self):
        return super(SaleReport, self)._group_by() + ', spa.country_id '
