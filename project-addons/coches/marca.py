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

from openerp.osv import orm, fields

class Marca(orm.Model):
	_name = "marca" # siempre comienza por barra-baja
	_description = "Marcas de coches" # Descripcción pro la que luego se puede buscar el modelo en openerp
	_columns = {
		'name': fields.char('Nnombre', size=150, required=True),
		'codigo' : fields.char('Codigo', size=8, required=True),
		'active' : fields.boolean('Active') # Tiene que ser active,name, state, sequence porque es el que reconoce openerp,
												# activo no valdria
	}
	_defaults = {
		'codigo' : 'MY',
		'active' : True
	} # Marca() se vería en versiones antiguas para cerrar la clase, en 7.0 ya no es necesario poner nada
	 #None es el null , por eso si llega null lo crea aunque este vacio
	def create(self, cr, uid, vals, context=None):
		if context is None: context = {}
		if vals.get('code', False) == '/':
			vals['code'] = self.pool.get('ir.sequence').get(cr, uid, 'marca.sequence')
		return super(Marca, self).create(cr, uid, vals, context=context)
