# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. Department All Rights Reserved
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

{
    'name': 'Lot tracking',
    'version': '1.0',
    'category': 'Warehouse',
    'summary' : 'Shows the paths that follow the lots of a product',
    'description': " //static/description/index.html//",
    'icon': '//static/src/img/icon.jpg//',
    'author': 'Pharmadus I.T. Department',
    'website': 'www.pharmadus.com',
    'depends': ['stock', 'quality_management_menu', 'custom_widths'],
    'data': [
        'views/lot_tracking_view.xml',
        'views/report_lot_tracking.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
