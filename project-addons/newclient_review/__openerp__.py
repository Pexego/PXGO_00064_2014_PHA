# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Marcos Ybarra Mayor <marcos.ybarra@pharmadus.com>$
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
    'name': "Newclient Review",
    'version': '1.0',
    'category': '',
    'description': """If a new client is added by a commercial, client will be in "Waiting for revision" until every data are reviewed by an authorized person.""",
    'author': 'Pharmadus I+D+i',
    'website': 'www.pharmadus.com',
    "depends" : ['base',
                 'sale'],
    "data" : ['newclient_review.xml'],
    "installable": True
}
