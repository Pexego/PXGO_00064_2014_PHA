# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models


class SaleReport(models.Model):
    _inherit = 'sale.report'

    notified_partner_id = fields.Many2one('res.partner', 'Cooperative')
    sale_type = fields.Selection(selection=[('normal', 'Normal'),
                                            ('sample', 'Sample'),
                                            ('transfer', 'Transfer'),
                                            ('replacement', 'Replacement'),
                                            ('intermediary', 'Intermediary')],
                                 string="Type")
    sale_channel_id = fields.Many2one('sale.channel', 'Canal de venta')
    product_categories = fields.Char('Product categories')
    commissions_parent_category = fields.Boolean('Has commission')

    def _select(self):
        select_str = ', s.notified_partner_id as notified_partner_id' + \
                     ', s.sale_type as sale_type' + \
                     ', s.sale_channel_id as sale_channel_id' + \
                     ', pc.name as product_categories' + \
                     ', cpc.commissions_parent_category'
        return super(SaleReport, self)._select() + select_str

    def _from(self):
        from_str = ' left join product_categ_rel pcr' + \
                   '   on pcr.product_id = p.id' + \
                   ' left join product_category pc' + \
                   '   on pc.id = pcr.categ_id' + \
                   ' left join product_category cpc' + \
                   '   on cpc.id = pc.parent_id'
        return super(SaleReport, self)._from() + from_str

    def _group_by(self):
        group_by_str = ', s.notified_partner_id, s.sale_type' + \
                       ', s.sale_channel_id, pc.name' + \
                       ', cpc.commissions_parent_category'
        return super(SaleReport, self)._group_by() + group_by_str
