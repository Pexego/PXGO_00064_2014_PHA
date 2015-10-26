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
#
##############################################################################

{
    'name': 'Product drop',
    'version': '1.0',
    'author': 'Pharmadus I+D+i',
    'summary' : ' Various modifications for show just what is needed ',
    'description': " //static/description/index.html//",
    'category': 'Warehouse',
    'website': 'www.pharmadus.com',
    'depends' : [
        'base',
        'product',
        'stock',
    ],
    'data' : [
        'data/initialization.xml',
        'views/product_drop.xml',
        'report/product_drop_report.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
