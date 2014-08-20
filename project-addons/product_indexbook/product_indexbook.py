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

from openerp.osv import osv, fields

class product_species(osv.Model):
    _name = 'product.species'
    _columns = {
        'name': fields.char('Name'),
        'macro_char': fields.char('Macro character'),
        'reference': fields.char('Reference')
    }

class product_template(osv.Model):
    _inherit = 'product.template'
    _columns = {
        'species_id': fields.many2one('product.species', 'Macro characters'),
        'reference': fields.related('species_id', 'reference', type='char', string='Reference to references\'s book')
    }

# Retouch object product.species to add relationship with product.template
class product_species(osv.Model):
    _inherit = 'product.species'
    _columns = {
        'product_id': fields.one2many('product.template', 'species_id', 'Products')
    }