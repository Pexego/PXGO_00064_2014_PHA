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

{
    'name': 'Custom reports',
    'version': '1.0',
    'author': 'Pharmadus I+D+i',
    'summary' : 'Odoo reports customized',
    'description': 'Odoo reports customized',
    'category': 'Reports',
    'website': 'www.pharmadus.com',
    'depends' : [
        'purchase',
        'report_webkit',
        'l10n_es_partner_mercantil',
        'sale_transfer',
        'sale_transfer_sample_rel',
        'sale_channel',
        'sale_promotions',
    ],
    'data' : [
        'data/report_paperformat.xml',
        'views/report_stockinventory.xml',
        'views/report_purchaseorder.xml',
        'views/report_saleorder.xml',
        'views/sale_report_view.xml',
    ],
    'installable': True
}
