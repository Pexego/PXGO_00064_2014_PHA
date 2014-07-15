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
#account.journal es el diario contable
class crear_factura(orm.TransientModel):
    _name = "crear.factura"
    _description = "Asistente para la creacion de la factura"

    _columns = {
        'journal_id': fields.many2one('account.journal', 'Journal', required=True),
        'partner_group':fields.boolean('Group by partner')
    }

    _defaults = {
        'partner_group':True
    }

    def crear_factura(self, cr, uid, ids, context=None):
        if context is None: context = {}
        obj = self.browse(cr, uid, ids[0]) # instancia del asistente
        invoices = {}
        created_invoices = []
        for expense in self.pool.get('gasto_flota').browse(cr, uid, context['active_ids']): #ver foto contexto en iphone
            if expense.empresa: # para comprobar que no venga vacio
                if obj.partner_group:
                    if invoices.get(expense.empresa.id, False):
                        invoices[expense.empresa.id].append(expense.id)
                    else:
                        invoices[expense.empresa.id] = [expense.id]
                else:
                    invoices[expense.id] = [expense.id]
                    
        for invoice in invoices:
            if obj.partner_group:
                partner = invoice;
            else:
                partner = self.pool.get('gasto_flota').browse(cr, uid, invoice).empresa.id
            partner = self.pool.get('res.partner').browse(cr, uid, partner)
            
            invoice_id = self.pool.get('account.invoice').create(cr, uid, {
                    'partner_id':partner.id,
                    'account_id':partner.property_account_payable.id,
                    'journal_id':obj.journal_id.id,
                    'type':'in_invoice'
                }, context = context) # Para ver los campos obligatorios a pasarle habria que mirar en faturas de openerp en modo desarrolllador
            created_invoices.append(invoice_id)

            #recorre las lineas de gastos
            for line in invoices[invoice]:
                line_obj = self.pool.get('gasto_flota').browse(cr, uid, line)
                product = line_obj.tipogasto_id.producto_id
                product_acc_id = product.property_account_expense and product.property_account_expense.id or False
                #En la liena anterior, el and hace lo siguiente: si product.property_account_expense existe le agrega el id, sino tira al OR 
                #si la linea anterior es false, salta el if not de debajo
                if not product_acc_id:
                    product_acc_id = product.categ_id.property_account_expense_categ and product.categ_id.property_account_expense_categ.id or False
                    if not product_acc_id:
                        raise orm.orm_except("Error","No tiene definida ninguna cuenta de gasto en el producto asociado %s" %(line_obj.tipogasto_id.name))
                invoice_line_id = self.pool.get('account.invoice.line').create(cr, uid, {
                    'product_id':product.id,
                    'name':line_obj.name or product.name,  #Si esta vacia la descripccopn coje la de tipo de gasto
                    'account_id':product_acc_id,
                    'quantity': line_obj.cantidad,
                    'price_unit':line_obj.precio_unidad,
                    'invoice_line_tax_id':[(6,0,[x.id for x in product.supplier_taxes_id])],#como es un campo many2many devuelve un diccionario, revisar transparencias para el 6,0
                    'invoice_id':invoice_id
                    }, context=context)
        self.pool.get('account.invoice').button_reset_taxes(cr, uid, created_invoices, context=context)
        return True
