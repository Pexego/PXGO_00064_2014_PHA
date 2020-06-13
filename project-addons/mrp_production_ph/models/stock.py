# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _, exceptions


class StockMove(models.Model):
    _inherit = 'stock.move'

    theorical_uom_qty = fields.Float(compute='_compute_theorical_uom_qty',
                                     string='Theorical qty.')

    @api.one
    def _compute_theorical_uom_qty(self):
        qty = 0
        pr = self.raw_material_production_id
        if pr:
            bl = pr.bom_id.bom_line_ids.filtered(
                lambda bl: bl.product_id == self.product_id)
            if bl:
                qty = bl.product_qty * pr.product_qty
        self.theorical_uom_qty = qty


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    production_state = fields.Selection([('draft', 'New'), ('cancel', 'Cancelled'),
        ('confirmed', 'Awaiting Raw Materials'), ('ready', 'Ready to Produce'),
        ('in_production', 'Production Started'), ('qty_set', 'Final quantity set'),
        ('released', 'Released'), ('done', 'Done'), ('n/a', '')],
                                        compute='_production_state')

    @api.one
    def _production_state(self):
        if self.lot_id.production_id:
            self.production_state = self.lot_id.production_id.state
        else:
            self.production_state = 'n/a'


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    transferred_with_barcodes = fields.Boolean(default=False)

    @api.multi
    def do_transfer_with_barcodes(self):
        self.ensure_one()
        if (self.picking_type_code == 'outgoing') and \
                (not (self.real_weight > 0) or not self.carrier_id or
                 not (self.number_of_packages > 0)):
            message = ''
            if not (self.real_weight > 0):
                message = _('Real weight to send must be greater than zero.\n')
            if not (self.number_of_packages > 0):
                message += _('Number of packages must be greater than zero.\n')
            if not (self.carrier_id):
                message += _('Carrier is not asigned.')
            raise exceptions.Warning(message)

        res_id = self.env['stock.transfer_details'].with_context({
                'active_ids': self.ids,
                'active_model': self._name
            }).create({
                'picking_id': self.id,
                'total_packages_expected': self.number_of_packages
            })
        view = self.env.ref('mrp_production_ph.view_transfer_with_barcodes_wizard')
        return {
            'name': 'Transferir con cód. de barras',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.transfer_details',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': res_id.id,
            'context': self.with_context({
                    'active_ids': self.ids,
                    'active_model': self._name,
                    'picking_type': self.picking_type_code
                }).env.context,
        }

class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    picking_transferred_wo_bc = fields.Text(compute='_compute_pick_trans_wo_bc')

    @api.multi
    def _compute_pick_trans_wo_bc(self):
        msg_title = _('A transfer without barcode has been used, and a manual '
                      'collection sheet must be provided on the pickings')
        for lot_id in self:
            message = False
            production_id = lot_id.production_id
            if production_id:
                # Gathering pickings
                picking_ids = production_id.hoard_ids.sudo().\
                    filtered(lambda p: p.state == 'done' and
                                       not p.transferred_with_barcodes)
                # Return pickings
                picking_ids += production_id.manual_return_pickings.sudo().\
                    filtered(lambda p: p.state == 'done' and
                                       not p.transferred_with_barcodes)
                # Create warning message
                if picking_ids:
                    message = '<p><b>' + msg_title + ':</b><br>' + \
                              ', '.join(picking_ids.mapped('name'))
            lot_id.picking_transferred_wo_bc = message