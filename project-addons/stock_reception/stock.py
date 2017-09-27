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
from openerp import models, fields, api
from lxml import etree

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

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(StockProductionLot, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if self._context.get('in_pick', False) and view_type=='form':
            arch = res['arch']
            doc = etree.XML(arch)
            for field in ['container_type', 'container_number', 'pallets']:
                node = doc.xpath("//field[@name='%s']" % field)[0]
                modifiers = node.get('modifiers')
                if not modifiers or modifiers == '{}':
                    modifiers = '{"required": true}'
                else:
                    modifiers = modifiers[:modifiers.rfind('}')] + ', "required": true' + '}'
                node.set('modifiers', modifiers)
            res['arch'] = etree.tostring(doc)
        return res



class StockPicking(models.Model):
    _inherit = 'stock.picking'

    supplier_delivery_note = fields.Char('Supplier delivery note')
    purchase_order = fields.Many2one('purchase.order', 'Purchase',
                                     related='move_lines.purchase_order_id')


class StockMove(models.Model):
    _inherit = 'stock.move'

    real_partner = fields.Char('Real partner',
                               related='picking_id.partner_id.name',
                               store=True)
    purchase_order_id = fields.Many2one('purchase.order', 'Purchase order',
                                        related='purchase_line_id.order_id')
