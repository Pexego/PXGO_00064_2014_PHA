# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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
    'name': 'Lot states',
    'version': '1.0',
    'category': 'stock',
    'description': """
        Se añaden los siguientes estados a los lotes: nuevo, en revision, revisado, aprobado, rechazado
        Se impide realizar un movimiento hasta que el lote no se encuentre en el estado apropiado

        Al rechazar el lote se crea un movimiento de la localizacion actual
        a rechazados. Desde rechazados existe la posibilidad de devolver el material al proveedor
        Se añade la posibilidad de consumir cuarentena en las producciones.

        """,
    'author': 'Pexego',
    'website': 'www.pexego.es',
    "depends": ['base', 'stock', 'product_expiry', 'mrp'],
    "data": ['wizard/lot_reject_partial.xml',
             'lot_view.xml', 'lot_workflow.xml',
             'mrp_view.xml', 'data/stock_location_data.xml', 'stock_view.xml'],
    "installable": True
}
