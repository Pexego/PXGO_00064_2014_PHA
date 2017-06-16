# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class ProductTimeAdviser(models.Model):
    _name = 'product.time.adviser'

    product_tmpl_id = fields.Many2one(comodel_name='product.template')
    type = fields.Selection([('fixed', 'Fixed time'),
                             ('variable', 'Variable time')],
                            string='Type', required=True)
    time = fields.Float(string='Time (seconds)', digits=(16,4))
    notes = fields.Char(string='Notes')
    sequence = fields.Integer(default=1)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    routing_ids = fields.Many2many(string='Production lines',
                                   comodel_name='mrp.routing',
                                   relation='product_mrp_routing_rel',
                                   column1='product_id',
                                   column2='routing_id')
    max_fixed = fields.Float(compute='_order_point_limits')
    min_fixed = fields.Float(compute='_order_point_limits')
    production_planning_qty = fields.Float(compute='_production_planning_qty')
    production_qty = fields.Float(compute='_production_qty')
    out_of_existences = fields.Float(compute='_out_of_existences')
    real_incoming_qty = fields.Float(compute='_real_incoming_qty')
    stock_by_day_i = fields.Float(string='Stock by day [I]', digits=(16, 2),
                                  readonly=True)
    stock_by_day_p = fields.Float(string='Stock by day [P]', digits=(16, 2),
                                  readonly=True)
    cons_by_day_i = fields.Float(string='Cons. by day [I]', digits=(16, 2),
                                 readonly=True)
    cons_by_day_p = fields.Float(string='Cons. by day [P]', digits=(16, 2),
                                 readonly=True)
    stock_by_day_i_ind = fields.Float(string='Stock by day [I] (indirect)',
                                      digits=(16, 2), readonly=True)
    stock_by_day_p_ind = fields.Float(string='Stock by day [P] (indirect)',
                                      digits=(16, 2), readonly=True)
    stock_by_day_p_ind_min = fields.Float(string='Minimum stock by day [P] (indirect)',
                                          digits=(16, 2), readonly=True)
    cons_by_day_i_ind = fields.Float(string='Cons. by day [I] (indirect)',
                                     digits=(16, 2), readonly=True)
    cons_by_day_p_ind = fields.Float(string='Cons. by day [P] (indirect)',
                                     digits=(16, 2), readonly=True)
    stock_by_day_i_total = fields.Float(
        string='Stock by day [I] (direct+indirect)', digits=(16, 2),
        readonly=True)
    stock_by_day_p_total = fields.Float(
        string='Stock by day [P] (direct+indirect)', digits=(16, 2),
        readonly=True)
    cons_by_day_i_total = fields.Float(
        string='Cons. by day [I] (direct+indirect)', digits=(16, 2),
        readonly=True)
    cons_by_day_p_total = fields.Float(
        string='Cons. by day [P] (direct+indirect)', digits=(16, 2),
        readonly=True)
    bom_member = fields.Boolean(string='BoM member?', compute='_bom_member')
    has_bom = fields.Boolean(compute='_has_bom')
    time_adviser = fields.One2many(comodel_name='product.time.adviser',
                                   inverse_name='product_tmpl_id')

    @api.multi
    def _has_bom(self):
        for p in self:
            p.has_bom = True if p.bom_ids else False

    @api.multi
    def _order_point_limits(self):
        for product in self:
            swo = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', product.id)
            ], order="id desc")
            if swo:
                if product.min_fixed != swo[0].product_min_qty:
                    product.min_fixed = swo[0].product_min_qty
                if product.max_fixed != swo[0].product_max_qty:
                    product.max_fixed = swo[0].product_max_qty

    @api.multi
    def _production_planning_qty(self):
        for product in self:
            pp_orders = self.env['production.planning.orders'].search([
                ('product_id', '=', product.id)
            ])
            qty = 0
            for o in pp_orders:
                qty += o.product_qty
            if product.production_planning_qty != qty:
                product.production_planning_qty = qty

    @api.multi
    def _production_qty(self):
        for product in self:
            prod_orders = self.env['mrp.production'].search([
                ('product_id', '=', product.id),
                ('state', 'not in', ('done', 'cancel')),
                ('move_created_ids', '!=', False)
            ])
            qty = 0
            for o in prod_orders:
                for m in o.move_created_ids:
                    qty += m.product_uom_qty
            if product.production_qty != qty:
                product.production_qty = qty

    @api.multi
    def _out_of_existences(self):
        warehouses = self.env['stock.warehouse'].search([])
        stock_ids = [wh.lot_stock_id.id for wh in warehouses]

        for product in self:
            quants = self.env['stock.quant'].search([
                ('product_id.product_tmpl_id', '=', product.id),
                ('location_id.usage', '=', 'internal'),
                ('location_id.scrap_location', '=', False),
                '!', ('location_id', 'child_of', stock_ids)
            ])
            product.out_of_existences = sum(quant.qty for quant in quants)

    @api.multi
    def _real_incoming_qty(self):
        for product in self:
            moves = self.env['stock.move'].search([
                ('product_id.product_tmpl_id', '=', product.id),
                ('picking_id.picking_type_id.code', '=', 'incoming'),
                ('location_id.usage', '!=', 'internal'),
                ('location_dest_id.usage', '=', 'internal'),
                ('state', 'in', ('assigned', 'confirmed', 'waiting'))
            ])
            product.real_incoming_qty = sum(move.product_uom_qty for move in moves)

    @api.multi
    def _bom_member(self):
        for p in self:
            bom_line_ids = self.env['mrp.bom.line'].search([
                ('product_id', 'in', p.product_variant_ids.ids),
                ('bom_id.active', '=', True),
                ('bom_id.product_id.active', '=', True)
            ])
            p.bom_member = True if bom_line_ids else False


class ProductProduct(models.Model):
    _inherit = 'product.product'

    @api.multi
    def create_production_planning_order(self):
        if not self.bom_ids:
            raise Warning(_('This product has no associated bill of materials'))

        if not self.routing_ids:
            raise Warning(_('This product has no associated production line'))

        order = self.env['production.planning'].orders.create({
            'product_id': self.id,
            'bom_id': self.bom_ids[0].id,
            'line_id': self.routing_ids[0].id
        })

        view_id = self.env.ref(
            'stock_available_ph.production_planning_new_order_form')
        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_model': 'production.planning.orders',
            'res_id': order.id,
            'target': 'new',
            'context': self.env.context,
        }