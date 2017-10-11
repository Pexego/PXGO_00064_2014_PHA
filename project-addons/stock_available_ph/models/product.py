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
    production_planning_qty = fields.Float(
        compute='_production_planning_qty',
        search='_search_production_planning_qty')
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
    cons_by_day_i_month = fields.Float(string='Cons. by day [I] (month)',
                                       compute='_cbd_i_period',
                                       digits=(16, 2),
                                       readonly=True)
    cons_by_day_i_semester = fields.Float(string='Cons. by day [I] (semester)',
                                          compute='_cbd_i_period',
                                          digits=(16, 2),
                                          readonly=True)
    cons_by_day_i_year = fields.Float(string='Cons. by day [I] (year)',
                                      compute='_cbd_i_period',
                                      digits=(16, 2),
                                      readonly=True)
    cons_by_day_p_month = fields.Float(string='Cons. by day [P] (month)',
                                       compute='_cbd_p_period',
                                       digits=(16, 2),
                                       readonly=True)
    cons_by_day_p_semester = fields.Float(string='Cons. by day [P] (semester)',
                                          compute='_cbd_p_period',
                                          digits=(16, 2),
                                          readonly=True)
    cons_by_day_p_year = fields.Float(string='Cons. by day [P] (year)',
                                      compute='_cbd_p_period',
                                      digits=(16, 2),
                                      readonly=True)
    bom_member = fields.Boolean(string='BoM member?', compute='_bom_member')
    has_bom = fields.Boolean(compute='_has_bom')
    time_adviser = fields.One2many(comodel_name='product.time.adviser',
                                   inverse_name='product_tmpl_id')
    stock_move_ids = fields.One2many(string='Stock movements',
                                     comodel_name='stock.move',
                                     inverse_name='product_id')
    production_planning_orders = fields.One2many(
        string='Production planning orders',
        comodel_name='production.planning.orders',
        inverse_name='product_id')

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
            qty = 0
            for o in product.production_planning_orders:
                qty += o.product_qty
            if product.production_planning_qty != qty:
                product.production_planning_qty = qty

    def _search_production_planning_qty(self, operator, value):
        return [('production_planning_orders.product_qty', operator, value)]

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

    @api.multi
    @api.depends('cons_by_day_i_total')
    def _cbd_i_period(self):
        for product in self:
            product.cons_by_day_i_month = product.cons_by_day_i_total * 30
            product.cons_by_day_i_semester = product.cons_by_day_i_total * 182.5
            product.cons_by_day_i_year = product.cons_by_day_i_total * 365

    @api.multi
    @api.depends('cons_by_day_p_total')
    def _cbd_p_period(self):
        for product in self:
            product.cons_by_day_p_month = product.cons_by_day_p_total * 30
            product.cons_by_day_p_semester = product.cons_by_day_p_total * 182.5
            product.cons_by_day_p_year = product.cons_by_day_p_total * 365


class ProductProduct(models.Model):
    _inherit = 'product.product'

    production_orders = fields.One2many(
        string='Production orders',
        comodel_name='mrp.production',
        inverse_name='product_id'
    )
#    domain = "[('state', 'not in', ('done', 'cancel')), ('move_created_ids', '!=', False)]"

    production_qty = fields.Float(compute='_production_qty')
    min_action = fields.Float(string='Minimum action quantity',
                              compute='_min_action')
    action_limit_exceeded = fields.Boolean(compute='_action_limit_exceeded',
                                           store=True)

    @api.multi
    def _production_qty(self):
        for product in self:
            production_orders = product.production_orders.\
                filtered(lambda r: r.state not in ('done', 'cancel') and
                                   r.move_created_ids != False)
            qty = 0
            for o in production_orders:
                for m in o.move_created_ids:
                    qty += m.product_uom_qty
            if product.production_qty != qty:
                product.production_qty = qty

#    def _search_production_qty(self, operator, value):
#        return [('production_orders.move_created_ids.product_uom_qty',
#                 operator, value)]

    @api.one
    def _min_action(self):
        orderpoint_id = self.env['stock.warehouse.orderpoint'].search([
            ('product_id', '=', self.id),
            ('from_date', '<=', fields.Date.today()),
            ('to_date', '>=', fields.Date.today())],
            order='id desc', limit=1)

        if not orderpoint_id:
            orderpoint_id = self.env['stock.warehouse.orderpoint'].search([
                ('product_id', '=', self.id),
                ('from_date', '=', False),
                ('to_date', '=', False)],
                order='id desc', limit=1)

        self.min_action = orderpoint_id.product_min_action_qty \
            if orderpoint_id else 0

    @api.one
    @api.depends('min_action', 'virtual_conservative')
    def _action_limit_exceeded(self):
        self.action_limit_exceeded = self.virtual_conservative < self.min_action

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