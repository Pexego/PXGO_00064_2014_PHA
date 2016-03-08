# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
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
#
##############################################################################
from openerp import models, fields


class ProcurementOrderAux(models.TransientModel):
    _name = 'procurement.order.aux'
    _inherits = {'procurement.order': 'procurement_id'}
    _description = 'Auxiliary procurement order'

    procurement_id = fields.Many2one(
        'procurement.order',
        'Procurement order',
        required=True,
        ondelete='cascade')
    uom_qty = fields.Float(default=0)
    uos_qty = fields.Float(default=0)
