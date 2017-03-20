# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
    'name': 'Product spec',
    'version': '8.0.1.2.0',
    'category': 'Product',
    'description': """
        The following fields are added to products:
            -line
            -subline
            -customer
            -clothing
            -country
            -packing internal
            -packing external
            -objective
            -container
            -base form


    """,
    'author': 'Pexego & Pharmadus',
    'website': '',
    "depends": ['product', 'quality_management_menu', 'purchase', 'stock', 'mrp'],
    "data": ['product_view.xml', 'security/ir.model.access.csv'],
    "installable": True
}
