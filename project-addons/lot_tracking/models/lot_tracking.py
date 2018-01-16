# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, tools


class StockLotMove(models.Model):
    _name = 'stock.lot.move'
    _auto = False
    _order = 'date'

    lot_id = fields.Many2one(comodel_name='stock.production.lot')
    move_id = fields.Many2one(comodel_name='stock.move', required=True,
                              ondelete='cascade')
    date = fields.Datetime(string='Date')
    product_uom = fields.Many2one(string='Unit of Measure',
                                  comodel_name='product.uom')
    location_id = fields.Many2one(string='Source Location',
                                  comodel_name='stock.location')
    location_dest_id = fields.Many2one(string='Destination Location',
                                       comodel_name='stock.location')
    partner_id = fields.Many2one(string='Partner', comodel_name='res.partner')
    picking_id = fields.Many2one(string='Reference',
                                 comodel_name='stock.picking')
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
                ['internal', 'view', 'procurement', 'transit']) and\
           (self.location_dest_id.usage in
                ['customer', 'inventory', 'supplier', 'production']):
            self.type = 'output'
        elif (self.location_id.usage in
                  ['customer', 'inventory', 'supplier', 'production']) and\
             (self.location_dest_id.usage in
                  ['internal', 'view', 'procurement', 'transit']):
            self.type = 'input'
        else:
            self.type = 'internal'

    def init(self, cr):
        tools.drop_view_if_exists(cr, self._table)
        cr.execute("""
            create view %s as (
                select
                    sqmr.move_id id,
                    spl.id lot_id,
                    sqmr.move_id,
                    sm.date,
                    sm.product_uom,
                    sm.location_id,
                    sm.location_dest_id,
                    sp.partner_id,
                    sp.id picking_id,
                    sm.state,
                    sum(sq.qty) qty
                from stock_production_lot spl
                join stock_quant sq on sq.lot_id = spl.id
                join stock_quant_move_rel sqmr on sqmr.quant_id = sq.id
                join stock_move sm on sm.id = sqmr.move_id
                left join stock_picking sp on sp.id = sm.picking_id
                group by 2, 1, 3, 4, 5, 6, 7, 8, 9, 10
                order by 2, 1       
            )
        """ % (self._table,))


class LotTracking(models.Model):
    _name = 'lot.tracking'
    _rec_name = 'product_id'

    product_id = fields.Many2one(comodel_name='product.product',
                                 domain="[('sequence_id', '!=', False)]")
    lot_id = fields.Many2one(comodel_name='stock.production.lot',
                             domain="[('product_id', '=', product_id)]")
    type_of_move = fields.Selection(string='Type of moves',
        selection=[('all', 'All movements'),('io', 'Inputs & Outputs')],
        default='io', required=True)

    lot_move_ids = fields.One2many(comodel_name='stock.lot.move',
                                   compute='_get_lot_moves')
    total = fields.Float(string='Total', compute='_get_total')
    company_id = fields.Many2one(comodel_name='res.company',
                                 related='product_id.company_id')

    @api.onchange('product_id')
    def clear_lot(self):
        self.lot_id = False

    @api.one
    def _get_lot_moves(self):
        if self.type_of_move == 'all':
            self.lot_move_ids = self.env['stock.lot.move'].\
                search([('lot_id', '=', self.lot_id.id)])
        else:
            self.lot_move_ids = self.env['stock.lot.move'].\
                search([
                    '&',
                    ('lot_id', '=', self.lot_id.id),
                    '|',
                    '&',
                    ('location_id.usage', 'in', ('internal', 'view', 'procurement', 'transit')),
                    ('location_dest_id.usage', 'in', ('customer', 'inventory', 'supplier', 'production')),
                    '&',
                    ('location_id.usage', 'in', ('customer', 'inventory', 'supplier', 'production')),
                    ('location_dest_id.usage', 'in', ('internal', 'view', 'procurement', 'transit'))
                ])

    @api.one
    def _get_total(self):
        total = 0
        for move in self.lot_move_ids:
            if move.type == 'input':
                total += move.qty
            elif move.type == 'output':
                total -= move.qty
        self.total = total

    @api.onchange('lot_id', 'type_of_move')
    def get_lot_moves(self):
        self._get_lot_moves()
        self._get_total()
