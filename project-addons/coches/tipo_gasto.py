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

class Tipo_gasto(orm.Model):
	_name = "tipo_gasto" # siempre comienza por barra-baja
	_description = "Tipo de gasto computable" # Descripcción pro la que luego se puede buscar el modelo en openerp
	_columns = {
		'name': fields.char('Tipo de gasto', size=150, required=True),
		'precio_unidad' : fields.float('Precio gasto unidad', digits=(16,2), required=True),		
		'producto_id' : fields.many2one('product.product', 'Productoo', required=True)
	}


	def onchange_product_id(self, cr, uid, ids, producto_id=False, context=None): # self, cr, uid son parametros que se pasan siempre al tipo de funcion on_change
																				#producto_id=false , si no recibe ningun argumento, producto vale false
		res={}
		if producto_id != False: #producto_id a secas significaria lo mismo
			product_obj = self.pool.get('product.product').browse(cr, uid, producto_id, context=context)

			res['value'] = {
				'precio_unidad' : product_obj.standard_price
			}
		return res

		
class gasto_flota(orm.Model):
	_inherit = "gasto_flota"
	_columns = {
		'tipogasto_id' : fields.many2one('tipo_gasto', 'Tipo de gasto', required=True)
	}
# Marca() se vería en versiones antiguas para cerrar la clase, en 7.0 ya no es necesario poner nada
