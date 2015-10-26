# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Marcos Ybarra<marcos.ybarra@pharmadus.com>$
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
    'name': "Custom permissions",
    'version': '1.0',
    'category': '',
    'summary' : ' Various modifications for show just what is needed and customize views to delete or add some fields',
    'description': " //static/description/index.html//",
    'author': 'Pharmadus I+D+i',
    'website': 'www.pharmadus.com',
    'depends' : ['sale'],
    'data' : ['views/sale_view.xml',
              'views/partner_view.xml',
              'security/groups.xml',
              'security/menus.xml'],
    'installable': True
}
