# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Business Applications
#    Copyright (c) 2011 OpenERP S.A. <http://openerp.com>
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
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
    'name': 'Practica coches',
    'version': '0.2',
    'category': 'Practicas',
    'description': """
First practice.
===============================================================

Testing how to developt an erp module, for ODOO.
    """,
    'author': 'Pharmadus SL',
    'website': 'http://www.pharmadus.com',
    'depends': ['base','product','account'],
    'icon': '/edi/static/src/img/knowledge.png',
    'images': [],
    'test': [],
    'js': [],
    'css': [],
    'data': ['marca_view.xml',
        'coche_view.xml',
        'gasto_flota.xml',
        'tipo_gasto.xml',
        'security/ir.model.access.csv',
        'data/coches_sequence.xml',
        'wizard/crear_factura_view.xml',
        'coches_report.xml'],
    'conflicts': [],
    'qweb': [],
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
