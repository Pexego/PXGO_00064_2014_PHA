# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
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

class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

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
                item['package'] = op.package
        return res

    @api.one
    def do_detailed_transfer(self):
        processed_ids = []
        # Create new and update existing pack operations
        for lstits in [self.item_ids, self.packop_ids]:
            for prod in lstits:
                pack_datas = {
                    'product_id': prod.product_id.id,
                    'product_uom_id': prod.product_uom_id.id,
                    'product_qty': prod.quantity,
                    'package_id': prod.package_id.id,
                    'lot_id': prod.lot_id.id,
                    'location_id': prod.sourceloc_id.id,
                    'location_dest_id': prod.destinationloc_id.id,
                    'result_package_id': prod.result_package_id.id,
                    'date': prod.date if prod.date else datetime.now(),
                    'owner_id': prod.owner_id.id,
                    'palet': prod.palet,
                    'package': prod.package,
                }
                if prod.packop_id:
                    prod.packop_id.with_context(no_recompute=True).write(pack_datas)
                    processed_ids.append(prod.packop_id.id)
                else:
                    pack_datas['picking_id'] = self.picking_id.id
                    packop_id = self.env['stock.pack.operation'].create(pack_datas)
                    processed_ids.append(packop_id.id)
        # Delete the others
        packops = self.env['stock.pack.operation'].search(['&', ('picking_id', '=', self.picking_id.id), '!', ('id', 'in', processed_ids)])
        packops.unlink()

        # Execute the transfer of the picking
        self.picking_id.do_transfer()

        # Create expedition if proceed
        self.picking_id.create_expedition()

        return True

    @api.multi
    def wizard_view(self):
        picking = self[0].picking_id
        if (picking.picking_type_code == 'outgoing') and \
                (not (picking.real_weight > 0) or not picking.carrier_id):
            message = ''
            if not (picking.real_weight > 0):
                message = _('Real weight to send must be greater than zero.\n')
            if not (picking.carrier_id):
                message += _('Carrier is not asigned.')
            raise exceptions.Warning(message)
        else:
            type = picking.picking_type_code
            return super(StockTransferDetails,
                         self.with_context(picking_type = type)).wizard_view()


class StockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    palet = fields.Integer('Palet', default=0)
    complete = fields.Integer('Complete',
                           compute='_recalculate_complete_and_rest',
                           readonly=True)
    package = fields.Integer('Package', default=0)
    rest = fields.Integer('Rest',
                           compute='_recalculate_complete_and_rest',
                           readonly=True)
    quantity_to_extract = fields.Float('Quantity to extract',
                           digits=dp.get_precision('Product Unit of Measure'),
                           default=0)

    @api.one
    @api.depends('product_id', 'quantity')
    def _recalculate_complete_and_rest(self):
        for rec in self:
            complete_qty = rec.product_id.product_tmpl_id.box_elements
            if complete_qty > 0:
                div = divmod(rec.quantity, complete_qty)
                rec.complete = div[0]
                rec.rest = div[1]
            else:
                rec.complete = 0
                rec.rest = self.quantity

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
            return self[0].split_wizard_view()

    @api.multi
    def do_split_quantities(self):
        for det in self:
            if det.quantity>1:
                det.quantity = (det.quantity-det.quantity_to_extract)
                new_id = det.copy(context=self.env.context)
                new_id.quantity = det.quantity_to_extract
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
