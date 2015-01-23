# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
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
    'name': "MRP review",
    'version': '1.0',
    'category': 'production',
    'description': """Adds the state review on mrp.production.""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['mrp'],
    "data": ['security/mrp_review_security.xml',
             'mrp_workflow.xml',
             'mrp_view.xml'],
    "installable": True
}
