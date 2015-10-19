# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pexego All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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


class StockContainerType(models.Model):
    _name = 'stock.container.type'

    name = fields.Char('Name')


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    container_type = fields.Many2one('stock.container.type', 'Container type')
    supplier_lot = fields.Char('Supplier lot')
    notes = fields.Text('Notes')
    date_in = fields.Date('Entry date')
    date_in_system = fields.Date('Entry date in system')
    reception_realized_by = fields.Char('Reception realized by')
    quantity = fields.Float('Quantity')
    uom_id = fields.Many2one('product.uom', 'UoM')
    container_number = fields.Integer('Number of containers')
    pallets = fields.Integer('Pallets')
    picking_exist = fields.Boolean('Picking exists')


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    supplier_delivery_note = fields.Char('Supplier delivery note')