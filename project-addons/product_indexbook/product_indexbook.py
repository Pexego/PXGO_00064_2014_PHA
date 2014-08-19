# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
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
##############################################################################
#

from openerp.osv import orm, fields

class product_species(orm.Model):
    _name = 'product.species'
    _columns = {
       'name': fields.char(help='Nombre'),
        'macro_char': fields.char(help='Carácter macro'),
        'reference': fields.char(help='Referencia a ficha en libro de referencias'),
    }

class product_template(orm.Model):
    _name = 'product.template'
    _inherit = 'product.template'
    _columns = {
        'macro_char': fields.one2many('product.species', 'name', 'macro_char'),
        'reference': fields.related('macro_char', 'reference'),
    }
