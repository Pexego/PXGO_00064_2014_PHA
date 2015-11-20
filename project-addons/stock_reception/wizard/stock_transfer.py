# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, exceptions, _
from lxml import etree


class StockTransferDetails(models.TransientModel):

    _inherit = 'stock.transfer_details'

    @api.model
    def fields_view_get(self, view_id=None, view_type='form', toolbar=False, submenu=False):
        res = super(StockTransferDetails, self).fields_view_get(
            view_id=view_id, view_type=view_type, toolbar=toolbar,
            submenu=submenu)
        if self._context.get('active_model', False) == 'stock.picking':
            picking_id = self._context.get('active_id', False)
            picking = self.env['stock.picking'].browse(picking_id)
        else:
            line = self.env[self._context['active_model']].browse(self._context['active_id'])
            picking  = line.transfer_id.picking_id
        if picking.picking_type_code == 'incoming':
            arch = res.get('fields', {}).get('item_ids', {}).get('views', {}).get('tree', {}).get('arch', '')
            if not arch:
                return res
            doc = etree.XML(arch)
            node_me = doc.xpath("//field[@name='lot_id']")[0]
            field_context = node_me.get('context')
            field_context = field_context[:field_context.rfind('}')] + ", 'in_pick': True" + '}'
            node_me.set('context', field_context)
            res['fields']['item_ids']['views']['tree']['arch'] = etree.tostring(doc)
        return res

    @api.one
    def do_detailed_transfer(self):
        if self.picking_id.picking_type_code == 'incoming':
            errors = False
            lot_errors = []
            for line in self.item_ids:
                if line.lot_id and self.picking_id.picking_type_code == 'incoming':
                    for field in ['container_type', 'quantity', 'uom_id', 'container_number', 'pallets']:
                        if not line.lot_id[field]:
                            errors = True
                            if line.lot_id.name not in lot_errors:
                                lot_errors.append(line.lot_id.name)
            if errors:
                raise exceptions.Warning(_('Field error'), _('Lots without reception data: %s') % ', '.join(lot_errors))
        return super(StockTransferDetails, self).do_detailed_transfer()


class StockTransferDetailsItems(models.TransientModel):

    _inherit = 'stock.transfer_details_items'

    is_incoming = fields.Boolean('Is incoming picking', compute='_get_incoming')

    @api.one
    def _get_incoming(self):
        self.is_incoming = self.transfer_id.picking_id.picking_type_code == 'incoming'
