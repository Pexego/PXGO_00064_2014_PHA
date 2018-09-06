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

{
    'name': 'Warehouse shipping light',
    'version': '1.0',
    'author': 'Pharmadus I+D+i',
    'summary' : 'Warehouse shipping (light version)',
    'description': 'Warehouse shipping (light version)',
    'category': 'Warehouse',
    'website': 'www.pharmadus.com',
    'depends' : [
        'sale',
        'stock',
        'delivery',
        'stock_reception',
        'custom_reports',
    ],
    'data' : [
        'data/report_paperformat.xml',
        'wizard/stock_transfer_details.xml',
        'views/report_stockpicking.xml',
        'views/report_delivery_note.xml',
        'views/report_container_labels.xml',
        'views/report_palet_labels.xml',
        'views/report_expeditions.xml',
        'views/sale_view.xml',
        'views/stock_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
