# -*- coding: utf-8 -*-
##############################################################################
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

{
    "name": "Partner Prospect",
    "version": "1.0",
    "author": "Pharmadus I+D+i",
    "summary": "Modifies OCA partner_prospect module to check Dimoni sales also",
    "description": "Modifies OCA partner_prospect module to check Dimoni sales also",
    "website": "http://www.pharmadus.com",
    "category": "Sales Management",
    "depends": [
        "sale",
        "partner_prospect",
    ],
    "data": [
        "views/res_partner_view.xml",
    ],
    "installable": True
}
