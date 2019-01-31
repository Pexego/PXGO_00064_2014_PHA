# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, tools


class StockLotMove(models.TransientModel):
    _name = 'stock.lot.move'
    _order = 'date'

    lot_tracking_id = fields.Many2one(comodel_name='lot.tracking')
    lot_id = fields.Many2one(comodel_name='stock.production.lot')
    move_id = fields.Many2one(comodel_name='stock.move')
    date = fields.Datetime(string='Date')
    product_uom = fields.Many2one(string='Unit of measure',
                                  comodel_name='product.uom')
    location_id = fields.Many2one(string='Source Location',
                                  comodel_name='stock.location')
    location_dest_id = fields.Many2one(string='Destination location',
                                       comodel_name='stock.location')
    partner_id = fields.Many2one(string='Partner', comodel_name='res.partner')
    picking_id = fields.Many2one(string='Reference',
                                 comodel_name='stock.picking')
    origin = fields.Char()
    state = fields.Selection(string='Status', selection=[
        ('draft', 'Draft'),
        ('cancel', 'Cancelled'),
        ('waiting', 'Waiting Another Operation'),
        ('confirmed', 'Waiting Availability'),
        ('partially_available', 'Partially Available'),
        ('assigned', 'Ready to Transfer'),
        ('done', 'Transferred'),
    ])
    qty = fields.Float(string='Quantity')
    type = fields.Char(compute='_check_type')

    @api.one
    def _check_type(self):
        if (self.location_id.usage in
                ['internal', 'view']) and\
           (self.location_dest_id.usage in
                ['customer', 'inventory', 'supplier', 'production', 'procurement', 'transit']):
            self.type = 'output'
        elif (self.location_id.usage in
                  ['customer', 'inventory', 'supplier', 'production', 'procurement', 'transit']) and\
             (self.location_dest_id.usage in
                  ['internal', 'view']):
            self.type = 'input'
        else:
            self.type = 'internal'

    @api.multi
    def action_show_origin(self):
        self.ensure_one()
        origin = self.origin
        if origin and origin[0:2] in ('PO', 'SO', 'MO'):
            if origin[0:2] == 'PO':
                model = 'purchase.order'
            elif origin[0:2] == 'SO':
                model = 'sale.order'
            else:
                model = 'mrp.production'

            order_id = self.env[model].search([('name', '=', origin.strip())])

            if order_id:
                return {
                    'type': 'ir.actions.act_window',
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': model,
                    'res_id': order_id.id,
                    'target': 'current',
                    'nodestroy': True,
                    'context': self.env.context
                }


class LotTracking(models.Model):
    _name = 'lot.tracking'
    _rec_name = 'product_id'
    _order = 'write_date desc'

    product_id = fields.Many2one(comodel_name='product.product',
                                 domain="[('sequence_id', '!=', False)]")
    lot_id = fields.Many2one(comodel_name='stock.production.lot',
                             domain="[('product_id', '=', product_id)]")
    type_of_move = fields.Selection(string='Type of moves',
        selection=[('all', 'All movements'),('io', 'Inputs & Outputs')],
        default='io', required=True)

    lot_move_ids = fields.One2many(comodel_name='stock.lot.move',
                                   inverse_name='lot_tracking_id',
                                   readonly=True)
    total = fields.Float(string='Total', readonly=True)
    company_id = fields.Many2one(comodel_name='res.company',
                                 related='product_id.company_id')

    @api.one
    def _get_lot_moves(self):
        if self.type_of_move == 'all':
            quant_ids = self.lot_id.quant_ids
            move_ids = quant_ids.mapped('move_ids')
        else:
            quant_ids = self.env['stock.quant']
            move_ids = self.env['stock.move']
            for quant_id in self.lot_id.quant_ids:
                for move_id in quant_id.move_ids:
                    if (move_id.location_id.usage in ('internal', 'view') and \
                        move_id.location_dest_id.usage in \
                        ('customer', 'inventory', 'supplier', 'production',
                         'procurement', 'transit')) \
                       or \
                       (move_id.location_id.usage in ('customer', 'inventory',
                           'supplier', 'production', 'procurement',
                           'transit') and \
                        move_id.location_dest_id.usage in ('internal', 'view')):
                        quant_ids |= quant_id
                        move_ids |= move_id

        self.lot_move_ids.unlink()
        for quant_id in quant_ids:
            for move_id in quant_id.move_ids:
                if move_id in move_ids:
                    lm_id = self.lot_move_ids.filtered(lambda m:
                        m.date == move_id.date and \
                        m.location_id == move_id.location_id and \
                        m.location_dest_id == move_id.location_dest_id
                    )
                    if lm_id:
                        lm_id.qty += quant_id.qty
                    else:
                        self.write({'lot_move_ids': [(0, 0, {
                            'lot_id': self.lot_id.id,
                            'move_id': move_id.id,
                            'date': move_id.date,
                            'product_uom': move_id.product_uom.id,
                            'location_id': move_id.location_id.id,
                            'location_dest_id': move_id.location_dest_id.id,
                            'partner_id': move_id.picking_id.partner_id.id,
                            'picking_id': move_id.picking_id.id,
                            'origin': move_id.picking_id.origin
                            if move_id.picking_id.origin else move_id.origin,
                            'state': move_id.state,
                            'qty': quant_id.qty
                        })]})

        total = 0
        for move_id in self.lot_move_ids:
            if move_id.type == 'input':
                total += move_id.qty
            elif move_id.type == 'output':
                total -= move_id.qty
        self.total = total

    @api.onchange('product_id')
    def clear_lot(self):
        self.lot_id = False
        self.clear_lot_moves()

    @api.onchange('lot_id', 'type_of_move')
    def clear_lot_moves(self):
        self.lot_move_ids = False
        self.total = 0

    @api.multi
    def get_traceability(self):
        self._get_lot_moves()
