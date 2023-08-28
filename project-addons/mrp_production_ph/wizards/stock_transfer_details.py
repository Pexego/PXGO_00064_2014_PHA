# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, exceptions
import openerp.addons.decimal_precision as dp


class StockTransferDetails(models.TransientModel):
    _inherit = 'stock.transfer_details'

    notes = fields.Text(compute='_get_notes', readonly=True)
    picking_weight = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'))

    @api.one
    def _get_notes(self):
        notes = ''
        origin = self.picking_id.origin
        if origin and origin[0:2] == 'MO':
            production_id = self.env['mrp.production'].\
                search([('name', '=', origin)])
            if production_id:
                notes = production_id.notes if production_id.notes else ''
                for p in self.env['stock.picking'].\
                        search([('origin', '=', production_id.name)]):
                    if p.note and p.note.strip() > '':
                        notes += (' | ' if notes else '') + p.note
            self.notes = notes

    @api.one
    def do_transfer_with_barcodes(self):
        errors = ''
        for item_id in self.item_ids:
            test_passed = True
            if item_id.product_id.categ_id.lot_assignment_by_quality_dept:
                test_passed = (
                    (item_id.lot_id.name and item_id.lot_barcode)
                    and
                    item_id.lot_id.name.strip().lower() ==
                    item_id.lot_barcode.strip().lower()
                )
            test_passed = test_passed or (
                self.env.context.get('picking_type') == 'outgoing'
                and
                (item_id.product_id.ean13 and item_id.lot_barcode)
                and
                item_id.product_id.ean13.strip() == item_id.lot_barcode.strip()
            )
            if not test_passed:
                errors += item_id.lot_id.name + ': ' + \
                          item_id.product_id.name + '\n'
        if errors:
            raise exceptions.Warning('Los siguientes lotes no coinciden:\n\n' +
                                     errors)
        else:
            self.picking_id.transferred_with_barcodes = True
            self.do_detailed_transfer()

    @api.multi
    def write(self, vals):
        if 'picking_weight' in vals:
            prod_id = self.env['mrp.production'].\
                search([('name', '=', self[0].picking_id.origin)])
            if prod_id:
                picking_weight = prod_id.picking_weight + vals['picking_weight']
                prod_id.write({'picking_weight': picking_weight})
        return super(StockTransferDetails, self).write(vals)


class StockTransferDetailsItems(models.TransientModel):
    _inherit = 'stock.transfer_details_items'

    lot_barcode = fields.Char()
    available_qty = fields.Float(compute='_get_available_qty', readonly=True)

    @api.one
    def _get_available_qty(self):
        move_ids = []
        if self.packop_id:
            for m in self.packop_id.picking_id.move_lines:
                if m.product_id == self.product_id:
                    move_ids += [m.id]
        available_quants = self.env['stock.quant'].search([
            ('lot_id', '=', self.lot_id.id),
            ('location_id', 'child_of', self.sourceloc_id.id),
            ('product_id', '=', self.product_id.id),
            ('qty', '>', 0),
            '|',
            ('reservation_id', '=', False),
            ('reservation_id', 'in', move_ids)])
        self.available_qty = sum(available_quants.mapped('qty'))

    @api.multi
    def action_copy_quantities(self):
        self.ensure_one()
        self.write({'quantity': self.available_qty})
        self.transfer_id.write({
            'picking_weight': self.transfer_id.picking_weight
        })
        view_id = self.env.\
            ref('mrp_production_ph.view_transfer_with_barcodes_wizard')
        window_action = {
            'name': 'Transferir con cód. de barras',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': self.transfer_id._name,
            'views': [(view_id.id, 'form')],
            'view_id': view_id.id,
            'target': 'new',
            'res_id': self.transfer_id.id,
            'context': self.with_context({
                'picking_type': 'internal',
                'for_production': self.name[:2] == 'MO',
            }).env.context,
        }
        return window_action
