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

class Coche(orm.Model):
	_name = "coche"
	_description = "Coches"
	_rec_name = "matricula"   # Al llamar desde gasto flota al coche, busca por defecto el name y lo muestra, si queremos mostrar otra cosa cdebemos de incluir esta linea, en este caso muestra la matrcula

	def name_get(self, cr, uid, ids, context=None):
		res = []
		for coche in self.browse(cr, uid, ids, context=context):
			name = coche.name+u' '+coche.matricula
			res.append((coche.id, name)) # Tupla, es el formato que utiliza openerp para el name_get
		return res

	def name_search(self, cr, user, name, args=None, operator='ilike', context=None, limit=100):
		if not args:
			args = []
		ids = self.search(cr, user, [('matricula', operator, name)]+ args, limit=limit, context=context)
		ids += self.search(cr, user, [('name', operator, name)]+ args, limit=limit, context=context)
		return self.name_get(cr, user, ids, context)

	_columns = {
		'matricula' : fields.char('Matriicula', size=12, required=True),
		'name' : fields.char('Nommbre', size=150, required=True),
		'bastidor_no' : fields.char('Nº de bastidor', size=40),
		'descripccion' : fields.text('Descripccion'),
		'active' : fields.boolean('Active'),
		'marca_id' : fields.many2one('marca', 'Mark', required=True)
	}
	_defaults = {
		'active' : True
	}
	
# Herencia simple y definimos nuevamente columns solo apra añadirle el campo one2many
# Herencia porque en init definimos que primero cargue marca, luego carga coche y luego carga lo nuevo de marca, el one to many
# Si no heredaramos asi, y agregaramos el one2many de Marca al propio .py, intentaria cargar un FK de coche y aun no estaria definido	
class Marca(orm.Model):
	_inherit = "marca"
	_columns = {
		'coche_ids' : fields.one2many('coche', 'marca_id', 'coches')
	}
