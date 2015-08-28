# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pharmadus I+D+i All Rights Reserved
#    $Iván Alvarez <informatica@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp.osv import fields, osv
from openerp.tools.translate import _


class mrp_bom_line(osv.osv):
    _inherit = 'mrp.bom.line'

    _columns = {
        'product_qty_available': fields.related('product_id', 'qty_available', type='float', string='Quantity On Hand',
                                                readonly=True),
    }
    _defaults = {
    }

mrp_bom_line()