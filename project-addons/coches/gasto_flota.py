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
import time

class Gasto_flota(orm.Model):
    _name = "gasto_flota"
    _description = "Gasto flota"

#calculo del subtotal (cantidad*precio unidad)
    def _get_subtotal(self, cr, uid, ids, field_name, arg, context=None):
        res = {}
        for expense_id in self.browse(cr, uid, ids, context=context):
            res[expense_id.id] = expense_id.cantidad * expense_id.precio_unidad #id la crea automaticamente openerp en la tabla
            
        return res
    
    _columns = {
        'coche_id' : fields.many2one('coche', 'Nombre coche', required=True),
        'cantidad' : fields.float('Cantidad', digits=(16,2), required=True),
        'precio_unidad' : fields.float('Precio unidad', digits=(16,2), required=True,group_operator="avg"),
        'name' : fields.text('Descripccion'),
        'empresa' : fields.many2one('res.partner', 'Empresa a la que pertenece', domain=[('supplier','=', True)]), # El dominio permite mostrar solo los proveedores, sino mostraria empresas tambien y mas 
        'date' : fields.datetime('Date', readonly=True),
        'subtotal' : fields.function(_get_subtotal, string='Cantidad total', type="float", digits=(16,2), readonly=True)
    }
    _defaults = {
        'cantidad' : 1.0, 
        'precio_unidad' : 1.0,
        'date':lambda *a: time.strftime("%Y-%m-%d %H:%M:%S") #Formato en el cual se guarda en la base de datos, al tener usuario en español openerp lo muestra luego en el formato español
    }

    def onchange_tipo_gasto_id(self, cr, uid, ids, tipogasto_id=False, context=None): # self, cr, uid son parametros que se pasan siempre al tipo de funcion on_change
                                                                                #tipogasto_id=false , si no recibe ningun argumento, producto vale false
        res={}
        if tipogasto_id != False: #producto_id a secas significaria lo mismo
            tipogasto_obj = self.pool.get('tipo_gasto').browse(cr, uid, tipogasto_id, context=context)

            #value, warning, domain son los tipos de campos que se pueden devolver
            res['value'] = {
                'precio_unidad' : tipogasto_obj.precio_unidad
            }
        return res
# Necesario para sacar el informe de los gastos asociados a un coche
class Coche(orm.Model):
    _inherit = "coche"
    _columns = {
        'gastos_flota_ids':fields.one2many('gasto_flota','coche_id',string='Gastos', readonly=True)
    }
