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
    'name': 'Product index book',
    'version': '2.0',
    'author': 'Pharmadus I+D+i',
    'description': 'Product index book',
    'category': 'Quality',
    'website': 'www.pharmadus.com',
    'depends' : [
        'base',
        'product',
        'stock',
        'purchase',
        'quality_management_menu',
    ],
    'data' : [
        'data/sequence.xml',
        'data/initialization.xml',
        'views/qc_species.xml',
        'views/qc_pis.xml',
        'views/product_template.xml',
        'views/stock_location.xml',
        'views/report_pis.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
