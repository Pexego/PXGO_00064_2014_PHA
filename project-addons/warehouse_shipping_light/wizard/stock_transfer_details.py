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

from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from datetime import datetime


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    total_packages = fields.Integer('Total packages', compute='_compute_counters')
    total_packages_expected = fields.Integer(readonly=True)
    total_palets = fields.Integer('Total palets', compute='_compute_counters')

    def recalculate_counters(self):
        package_list = [] # Count different packages
        palet_list = []   # Count different palets
        completes = 0     # Sum completes
        for item in self.item_ids:
            if item.package > 0 and not item.package in package_list:
                package_list.append(item.package)
            if item.palet > 0 and not item.palet in palet_list:
                palet_list.append(item.palet)
            completes += item.complete
        self.total_packages = len(package_list) + completes
        self.total_palets = len(palet_list)

    @api.one
    @api.depends('item_ids',
                 'item_ids.package',
                 'item_ids.palet')
    def _compute_counters(self):
        self.recalculate_counters()

    @api.onchange('item_ids')
    def onchange_complete(self):
        self.recalculate_counters()

    @api.multi
    def wizard_view(self):
        picking = self[0].picking_id
        if (picking.picking_type_code == 'outgoing') and \
                (not (picking.real_weight > 0) or not picking.carrier_id or
                 not (picking.number_of_packages > 0)):
            message = ''
            if not (picking.real_weight > 0):
                message = _('Real weight to send must be greater than zero.\n')
            if not (picking.number_of_packages > 0):
                message += _('Number of packages must be greater than zero.\n')
            if not (picking.carrier_id):
                message += _('Carrier is not asigned.')
            raise exceptions.Warning(message)
        else:
            type = picking.picking_type_code
            self.total_packages_expected = picking.number_of_packages
            return super(StockTransferDetails,
                         self.with_context(picking_type=type)).wizard_view()

    @api.model
    def default_get(self, fields):
        res = super(StockTransferDetails, self).default_get(fields)

        picking = self.env['stock.picking'].browse(
            self.env.context.get('active_id', False))
        pack_operation = self.env['stock.pack.operation']
        if picking.picking_type_code == 'outgoing':
            for item in res.get('item_ids', []):
                if not item['packop_id']:
                    continue
                op = pack_operation.browse(item['packop_id'])
                item['palet'] = op.palet
                item['complete'] = op.complete if op.complete else 0
                item['package'] = op.package
                if op.complete:
                    item['rest'] = op.product_qty - (op.complete *
                                     op.product_id.product_tmpl_id.box_elements)
                else:
                    item['rest'] = op.product_qty
        return res

    @api.one
    def do_detailed_transfer(self):
        # Check equality of total packages and number of packages before...
        if self.picking_id.picking_type_code == 'outgoing':
            if self.picking_id.number_of_packages > self.total_packages:
                raise exceptions.Warning(_(
                   'Total packages is minor than specified in carrier details'
                ))
            elif  self.picking_id.number_of_packages < self.total_packages:
                raise exceptions.Warning(_(
                   'Total packages is greater than specified in carrier details'
                ))

        res = super(StockTransferDetails, self).do_detailed_transfer()

        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                complete = prod.complete if prod.complete else 0
                if complete:
                    rest = prod.quantity - (prod.complete *
                                   prod.product_id.product_tmpl_id.box_elements)
                else:
                    rest = prod.quantity

                prod.packop_id.with_context(no_recompute=True).write(
                    {
                        'palet': prod.palet,
                        'complete': complete,
                        'package': prod.package,
                        'rest': rest,
                        'transfer_detail_item': prod.id
                    }
                )

        # Create expedition if proceed
        self.picking_id.create_expedition()

        return res


class StockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'
    _order = 'product_id, id'

    palet = fields.Integer('Palet', default=0)
    complete = fields.Integer('Complete', default=0)
    package = fields.Integer('Package', default=0)
    rest = fields.Float('Rest', readonly=True)
    quantity_to_extract = fields.Float('Quantity to extract',
                           digits=dp.get_precision('Product Unit of Measure'),
                           default=0)
    active = fields.Boolean('Active', default=True)
    name = fields.Char(related='packop_id.linked_move_operation_ids.move_id.name',
                       readonly=True)
    product_uom_category_id = fields.Integer(compute='_get_uom_category_id')

    @api.one
    def _get_uom_category_id(self):
        self.product_uom_category_id = self.product_uom_id.category_id.id

    @api.onchange('quantity', 'complete')
    def onchange_complete(self):
        message = False

        gtin14_id = self.product_id.\
            gtin14_partner_specific(self.transfer_id.picking_id.partner_id) if \
            self.transfer_id else False
        complete_qty = gtin14_id.units if gtin14_id else \
            self.product_id.box_elements

        if complete_qty > 0:
            required_qty = self.complete * complete_qty
            if required_qty > self.quantity:
                self.complete = 0
                self.rest = self.quantity
                message = _('Insufficient quantity to satisfy the required complete units!')
            else:
                self.complete = self.complete
                self.rest = self.quantity - required_qty
        else:
            self.complete = 0
            message = _('Complete qty is not defined for this product!')

        res = {}
        if message:
            res['warning'] = {'title': _('Warning'), 'message': message}
        return res

    @api.multi
    def split_wizard_view(self):
        view = self.env.ref('warehouse_shipping_light.view_transfer_split_config')

        return {
            'name': _('Enter quantity of the new line'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.transfer_details_items',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context,
        }

    @api.multi
    def split_quantities(self):
        if self and self[0]:
            self.complete = 0
            return self[0].split_wizard_view()

    @api.multi
    def do_split_quantities(self):
        for det in self:
            if det.quantity > 0:
                det.quantity = (det.quantity-det.quantity_to_extract)
                det.rest = det.quantity
                new_id = det.copy(context=self.env.context)
                new_id.quantity = det.quantity_to_extract
                new_id.rest = new_id.quantity
                new_id.quantity_to_extract = 0
                new_id.packop_id = False
                det.quantity_to_extract = 0
        if self and self[0]:
            return self[0].transfer_id.wizard_view()

    @api.multi
    def do_not_split_quantities(self):
        for det in self:
            det.quantity_to_extract = 0
        if self and self[0]:
            return self[0].transfer_id.wizard_view()

    @api.multi
    def unlink(self):
        if not self._context:
            return super(StockTransferDetailsItems, self).unlink()
        else:
            for line in self:
                line.active = False
