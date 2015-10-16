# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus I+D+i All Rights Reserved
#    $Iván Alvarez <informatica@pharmadus.com>$
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
    'name': "Sale channels",
    'version': '1.0',
    'category': 'sale',
    'description': """Adds the management for sale channels""",
    'icon': '/sale_channel/static/src/img/icon.png',
    'author': 'Pharmadus I+D+i',
    'website': 'www.pharmadus.com',
    "depends": ['sale'],
    "data": [
        'sale_channel_view.xml',
        'sale_channel_extra_view.xml',
        'sale_channel_invoice_report.xml',
        'security/ir.model.access.csv'
    ],
    "installable": True
}

