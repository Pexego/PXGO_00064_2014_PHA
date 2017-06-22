# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, SUPERUSER_ID, _, exceptions


class StockMove(models.Model):
    _inherit = 'stock.move'

    lots_string = fields.Char(string='Lots', readonly=True, index=True)
    categ_ids = fields.Many2many(related='product_id.categ_ids')
    purchase_amount = fields.Float(related='purchase_line_id.gross_amount')
    purchase_expected_date = fields.Date(related='picking_id.purchase_order.minimum_planned_date')

    @api.multi
    def _get_related_lots_str(self):
        for move in self:
            lot_str = u", ".join([x.name for x in move.lot_ids])
            if move.lots_string != lot_str:
                move.lots_string = lot_str

    @api.multi
    def write(self, vals):
        res = super(StockMove, self).write(vals)
        for move in self:
            if len(move.lot_ids) > 0:
                self._get_related_lots_str()
        return res

    def init(self, cr):
        move_ids = self.search(cr, SUPERUSER_ID,
                               [('lots_string', 'in', (False, ''))])
        moves = self.browse(cr, SUPERUSER_ID, move_ids)
        moves._get_related_lots_str()


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    address_city = fields.Char(related='partner_id.city')
    address_zip = fields.Char(related='partner_id.zip')
    address_country = fields.Char(related='partner_id.country_id.name')
    picking_type_desc = fields.Char(compute='_compute_picking_type_desc')

    @api.one
    @api.depends('picking_type_id')
    def _compute_picking_type_desc(self):
        types = {'outgoing': ' - (Albarán de salida)',
                 'incoming': ' - (Albarán de entrada)',
                 'internal': ' - (Albarán interno)'}
        self.picking_type_desc = types.get(self.picking_type_id.code, '')

    @api.multi
    def _check_reserved_quantities(self):
        unmatched_quantities_found = False
        for picking in self:
            for move in picking.move_lines:
                unmatched_quantities_found = unmatched_quantities_found or \
                    move.partially_available
                if not unmatched_quantities_found:
                    sum = 0
                    for quant in move.reserved_quant_ids:
                        sum += quant.qty
                    diff = abs(sum - move.product_qty)
                    unmatched_quantities_found = diff > 0.001

        if unmatched_quantities_found:
            return self.env['custom.views.warning'].show_message(
                _('Stock assignment warning'),
                _('WARNING: There are stock reservations that do not match!')
            )
        return False

    @api.multi
    def action_assign(self):
        res = super(StockPicking, self).action_assign()
        return self._check_reserved_quantities() or res

    @api.multi
    def rereserve_pick(self):
        super(StockPicking, self).rereserve_pick()
        return self._check_reserved_quantities()

    @api.multi
    def confirm_action_cancel(self):
        view = self.env.ref('custom_views.custom_views_picking_cancel_confirm_form')
        return {
            'name': _('Confirm picking cancellation'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'stock.picking',
            'views': [(view.id, 'form')],
            'view_id': view.id,
            'target': 'new',
            'res_id': self.id,
        }


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    lot_state = fields.Selection(string='Lot state', related='lot_id.state')

    @api.multi
    def unlink(self):
        if self._context.get('nodelete', False):
            raise exceptions.Warning(_('Deletion avoided'),
                                     _('Quants erasing is not allowed'))
        return super(StockQuant, self).unlink()


class StockHistory(models.Model):
    _inherit = 'stock.history'

    categ_ids = fields.Many2many(related='product_id.categ_ids')


class StockProductionLot(models.Model):
    _inherit = 'stock.production.lot'

    default_code = fields.Char(related='product_id.default_code', store=True)
    categ_id = fields.Many2one(related='product_id.categ_id', store=True)
    categ_ids = fields.Many2many(related='product_id.categ_ids', store=True)
    available_stock = fields.Float(string='Available stock',
                                   compute='_available_stock')

    @api.one
    def _available_stock(self):
        quantity = 0
        for q in self.quant_ids:
            if q.location_id.usage in ('internal', 'procurement', 'transit',
                                       'view'):
                quantity += q.qty
        self.available_stock = quantity
