# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
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
    'name': 'Product under minimuns (extended)',
    'version': '1.0',
    'category': 'Warehouse',
    'description': """
        Adds a new field that computes the relation between stock & sales by day for each product.
    """,
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': ['product_stock_unsafety', 'custom_views'],
    'data': [
        'views/product_view.xml',
        'views/product_stock_unsafety_view.xml',
        'wizard/product_stock_by_day.xml',
        'wizard/bom_member_of.xml',
    ],
    'installable': True
}
