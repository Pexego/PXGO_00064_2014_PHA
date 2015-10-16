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
    'name': "Relation transfer and sample",
    'version': '1.0',
    'category': 'sale',
    'description': """
                      -Añade campos comunes para transfers y muestras,
                      -Añade el domain para que no se muestren samples/transfer en pedidos y presupuestos.
                      -Añade campos para filtrar y agrupar por samples/transfer en el informe de ventas.
                      -Añade un selection oculto para poder agrupar por tipo.
                      -Se añade un menú para poder ver las ventas de todos los tipos.
                   """,
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['sale',
                'sale_transfer',
                'sale_samples',
                'sale_replacement',
                'sale_intermediary'],

    "data": ['sale_view.xml'],
    "installable": True
}
