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
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.    If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import fields, models


class sale_report(models.Model):
    _inherit = 'sale.report'

    notified_partner_id = fields.Many2one('res.partner', 'Cooperative')
    sale_type = fields.Selection(selection=[('normal', 'Normal'),
                                            ('sample', 'Sample'),
                                            ('transfer', 'Transfer'),
                                            ('replacement', 'Replacement'),
                                            ('intermediary', 'Intermediary')],
                                 string="Type")
    sale_channel_id = fields.Many2one('sale_channel', 'Canal de venta')

    def _select(self):
        select_str = ', s.notified_partner_id as notified_partner_id' + \
                     ', s.sale_type as sale_type, s.sale_channel_id as sale_channel_id'
        return super(sale_report, self)._select() + select_str

    def _group_by(self):
        group_by_str = ',s.notified_partner_id, s.sale_type, s.sale_channel_id'
        return super(sale_report, self)._group_by() + group_by_str