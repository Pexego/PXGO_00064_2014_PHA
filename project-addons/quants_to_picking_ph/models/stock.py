# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.multi
    def quants_to_picking(self):
        e = self.env
        picking_type = e.ref('stock.picking_type_internal') if \
            e.ref('stock.picking_type_internal') else \
            e.ref('__export__.stock_picking_type_16') if \
            e.ref('__export__.stock_picking_type_16') else \
            e.ref('__export__.stock_picking_type_21') if \
            e.ref('__export__.stock_picking_type_21') else \
            e.ref('__export__.stock_picking_type_11') if \
            e.ref('__export__.stock_picking_type_11') else False

        location_dest_id = self.env.user.company_id.\
            internal_transit_location_id
        picking = self.env['stock.picking'].create({
            'invoice_state': 'none',
            'move_type': 'direct',
            'picking_type_id': picking_type.id,
            'state': 'draft'
        })

        # Create moves from selected quants
        moves = self.env['stock.move']
        for quant in self:
            moves.create({
                'invoice_state': 'none',
                'location_dest_id': location_dest_id.id,
                'location_id': quant.location_id.id,
                'name': quant.product_id.name,
                'picking_id': picking.id,
                'picking_type_id': picking_type.id,
                'procure_method': 'make_to_stock',
                'product_id': quant.product_id.id,
                'product_uom': quant.product_id.uom_id.id,
                'product_uom_qty': quant.qty,
                'state': 'draft',
                'restrict_lot_id': quant.lot_id.id,
            })

        # Returns the new created picking
        return {
            'picking_id': picking.id,
            'location_dest_id': location_dest_id.id
        }