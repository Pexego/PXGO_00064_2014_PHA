# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, exceptions, _
import openerp.addons.decimal_precision as dp
from openerp.tools.float_utils import float_round


class StockMoveAssignManualLot(models.TransientModel):

    _name = 'stock.move.assign.manual.lot'

    line_ids = fields.One2many('stock.move.assign.manual.lot.line',
                               'wizard_id', 'Lines')
    lines_qty = fields.Float(
        string='Reserved qty', compute='_compute_qties',
        digits=dp.get_precision('Product Unit of Measure'))
    move_qty = fields.Float(string='Remaining qty', compute='_compute_qties',
                            digits=dp.get_precision('Product Unit of Measure'))

    @api.depends('line_ids', 'line_ids.use_qty')
    def _compute_qties(self):
        move = self.env['stock.move'].browse(self.env.context['active_id'])
        lines_qty = sum(self.line_ids.filtered(
            lambda r: r.use_qty > 0).mapped('use_qty'))
        self.lines_qty = lines_qty
        self.move_qty = float_round(
            move.product_uom_qty, precision_rounding=move.product_uom.rounding,
            rounding_method='UP') - lines_qty

    @api.model
    def default_get(self, var_fields):
        super(StockMoveAssignManualLot, self).default_get(var_fields)
        move = self.env['stock.move'].browse(self.env.context['active_id'])
        available_quants = self.env['stock.quant'].search([
            ('location_id', 'child_of', move.location_id.id),
            ('product_id', '=', move.product_id.id),
            ('qty', '>', 0),
            '|',
            ('reservation_id', '=', False),
            ('reservation_id', '=', move.id)
        ])
        lots = {}
        for quant in available_quants:
            if quant.lot_id.id not in lots:
                lots[quant.lot_id.id] = [0.0, 0.0]
            if quant.reservation_id:
                lots[quant.lot_id.id][1] += quant.qty
            lots[quant.lot_id.id][0] += quant.qty
        lines = []
        for lot in lots.keys():
            if move.product_id.raw_material and move.is_hoard_move and not \
                    move.picking_id.accept_multiple_raw_material:
                if lots[lot][0] < move.product_uom_qty:
                    continue
            lines.append({
                'lot_id': lot,
                'available_qty': lots[lot][0],
                'use_qty': lots[lot][1]
            })
        return {'line_ids': lines}

    @api.multi
    @api.constrains('line_ids')
    def check_qty(self):
        for record in self:
            if record.line_ids:
                move = self.env['stock.move'].browse(
                    self.env.context['active_id'])
                if record.lines_qty != float_round(
                        move.product_uom_qty,
                        precision_rounding=move.product_uom.rounding,
                        rounding_method='UP'):
                    raise exceptions.Warning(
                        _('Quantity is different than the needed one'))

    @api.multi
    def assign_lots(self):
        self.ensure_one()
        move = self.env['stock.move'].browse(self.env.context['active_id'])
        if move.product_id.raw_material and move.is_hoard_move and not \
                move.picking_id.accept_multiple_raw_material and \
                len(self.line_ids.filtered(lambda r: r.use_qty > 0)) > 1:
            raise exceptions.Warning(
                _('Multiple lot'),
                _('The production route only accepts one lot of raw material'))
        move.picking_id.mapped('pack_operation_ids').unlink()
        for quant_id in move.reserved_quant_ids.ids:
            move.write({'reserved_quant_ids': [[3, quant_id]]})
        quants = []
        for line in self.line_ids.filtered(lambda r: r.use_qty > 0):
            available_quants = self.env['stock.quant'].search([
                ('lot_id', '=', line.lot_id.id),
                ('location_id', 'child_of', move.location_id.id),
                ('product_id', '=', move.product_id.id),
                ('qty', '>', 0),
                '|',
                ('reservation_id', '=', False),
                ('reservation_id', '=', move.id)
            ])

            needed_qty = line.use_qty
            for quant in available_quants:
                quant_qty = quant.qty
                if needed_qty < quant_qty:
                    quant_qty = needed_qty
                quants.append((quant, quant_qty))
                needed_qty -= quant_qty
                if needed_qty <= 0:
                    break
        self.pool['stock.quant'].quants_reserve(
            self.env.cr, self.env.uid, quants, move, context=self.env.context)
        move.create_return_operations()
        return {'type': 'ir.actions.act_window_close'}


class StockMoveAssignManualLotLine(models.TransientModel):

    _name = 'stock.move.assign.manual.lot.line'

    wizard_id = fields.Many2one('stock.move.assign.manual.lot')
    lot_id = fields.Many2one('stock.production.lot', 'Lot')
    available_qty = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'))
    use_qty = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'))

    @api.onchange('use_qty')
    def onchange_use_qty(self):
        if self.use_qty > self.available_qty:
            raise exceptions.Warning(
                _('Quantity error'),
                _('Quantity is higher than the available'))
