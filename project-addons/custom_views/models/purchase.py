# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    discount_from_external_storage = fields.Boolean(default=False)

    @api.multi
    def duplicate(self):
        res = self.copy()
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self._name,
            'res_id': res.id,
            'target': 'current',
            'flags': {'initial_mode': 'edit'},
            'nodestroy': True,
            'context': self.env.context
        }

    @api.multi
    def confirm_purchase_order(self):
        res = self.signal_workflow('purchase_confirm')
        if self.discount_from_external_storage:
            # Disable invoicing for incoming picking
            incoming_picking_id = self.mapped('all_picking_ids').\
                filtered(lambda r: r.picking_type_code == 'incoming')
            if incoming_picking_id:
                incoming_picking_id.invoice_state = 'none'

            # Create new picking to get rid of supplier stock
            picking_id = self.env['stock.picking'].create({
                'picking_type_id': self.env.ref('stock.picking_type_internal').id,
                'invoice_state': 'none',
                'origin': self.name,
                'partner_id': self.partner_id.id,
                'supplier_delivery_note': self.name
            })
            for line in self.order_line:
                self.env['stock.move'].create({
                    'picking_id': picking_id.id,
                    'picking_type_id': picking_id.picking_type_id.id,
                    'origin': self.name,
                    'partner_id': line.partner_id.id,
                    'purchase_line_id': line.id,
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'product_uom': line.product_uom.id,
                    'product_uom_qty': line.product_qty,
                    'price_unit': line.price_unit,
                    'location_id': self.env.\
                        ref('__export__.stock_location_102').id,
                    'location_dest_id': self.env.\
                        ref('stock.location_inventory').id
                })

            action_data = self.env.ref('stock.action_picking_tree').read()[0]
            form_view = self.env.ref('stock.view_picking_form')
            action_data['views'] = [(form_view.id, 'form')]
            action_data['res_id'] = picking_id.id
            action_data['context'] = {}
            return action_data
        return res

class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    date_done = fields.Date()