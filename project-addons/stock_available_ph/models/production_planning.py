# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning
from datetime import datetime, timedelta
from pytz import timezone


class ProductionPlanning(models.Model):
    _name = 'production.planning'
    _description = 'Production planning of stock needed to produce'

    name = fields.Char('Production planning')


class ProductionPlanningOrders(models.Model):
    _name = 'production.planning.orders'
    _description = 'Planning of orders to produce'

    name = fields.Char(compute='_compound_name')
    date_start = fields.Datetime(string='Start date',
                                 default=lambda r: fields.Datetime.now(),
                                 required=True)
    date_end = fields.Datetime(string='End date',
                               default=lambda r: fields.Datetime.now(),
                               required=True)
    estimated_time = fields.Float(string='Esimated time',
                                  compute='_estimated_time',
                                  readonly=True)
    recommended_time = fields.Float(string='Recommended time',
                                    compute='_recommended_time',
                                    readonly=True)
    product_id = fields.Many2one(string='Final product',
                                 comodel_name='product.product',
                                 domain="[('bom_ids', '!=', False),"
                                        " ('bom_ids.type', '!=', 'phantom'),"
                                        " ('obsolete', '=', False)]",
                                 required=True)
    default_code = fields.Char(related='product_id.default_code',
                               readonly=True)
    product_tmpl_id = fields.Many2one(related='product_id.product_tmpl_id',
                                      readonly=True)
    bom_id = fields.Many2one(string='Bills of materials',
                             comodel_name='mrp.bom',
                             domain="[('product_tmpl_id', '=', product_tmpl_id)]",
                             required=True)
    line_id = fields.Many2one(string='Line',
                              comodel_name='mrp.routing',
                              domain="[('product_ids', 'in', product_tmpl_id)]",
                              required=True)
    product_qty = fields.Integer(string='Quantity to predict')
    production_planning = fields.Many2one(comodel_name='production.planning',
                                          ondelete='cascade',
                                          readonly=True)
    compute = fields.Boolean(string='Compute', default=True)
    stock_status = fields.Selection([('ok', 'Available'),
                                     ('out', 'Out of stock'),
                                     ('incoming', 'Incoming'),
                                     ('no_stock', 'Not available')],
                                    string='Stock status', default='ok')
    production_order = fields.Many2one(comodel_name='mrp.production',
                                       readonly=True)
    note = fields.Char(string='Note for production')
    cons_by_day_p_total = fields.Float(related='product_id.cons_by_day_p_total',
                                       readonly=True)
    cons_by_day_p_month = fields.Float(related='product_id.cons_by_day_p_month',
                                       readonly=True)
    cons_by_day_p_semester = fields.Float(related='product_id.cons_by_day_p_semester',
                                          readonly=True)
    cons_by_day_p_year = fields.Float(related='product_id.cons_by_day_p_year',
                                      readonly=True)
    cons_by_day_i_total = fields.Float(related='product_id.cons_by_day_i_total',
                                       readonly=True)
    cons_by_day_i_month = fields.Float(related='product_id.cons_by_day_i_month',
                                       readonly=True)
    cons_by_day_i_semester = fields.Float(related='product_id.cons_by_day_i_semester',
                                          readonly=True)
    cons_by_day_i_year = fields.Float(related='product_id.cons_by_day_i_year',
                                      readonly=True)
    uom_id = fields.Many2one(related='product_id.uom_id', readonly=True)
    active = fields.Boolean(default=True)

    @api.multi
    def _compound_name(self):
        for order in self:
            if order.default_code == 'Gen0001':
                order.name =  u'{} ({:d}) PR{:d}'.\
                    format(order.note, order.product_qty, order.id)
            elif self.env.context.get('show_only_order_id', False):
                order.name = u'PR{:d}'.format(order.id)
            else:
                order.name =  u'{} ({:d}) PR{:d}'.\
                    format(order.product_id.name, order.product_qty, order.id)

    @api.onchange('product_id')
    def product_id_change(self):
        bom_dom = [('product_tmpl_id', '=', self.product_tmpl_id.id)]
        bom_ids = self.env['mrp.bom'].search(bom_dom)
        self.bom_id = bom_ids[0] if bom_ids else False

        self.line_id = False

        res = {'domain': {'line_id': False}}
        if self.product_id.routing_ids:
            res['domain']['line_id'] = [('product_ids', 'in',
                                         self.product_id.product_tmpl_id.id)]
        else:
            res['domain']['line_id'] = [('wildcard_route', '=', True)]
        return res

    @api.onchange('date_start')
    def check_date_end(self):
        if self.date_start > self.date_end:
            self.date_end = self.date_start

    @api.onchange('date_end')
    def check_date_start(self):
        if self.date_start > self.date_end:
            self.date_start = self.date_end

    @api.one
    def _estimated_time(self):
        date_start_utc = fields.Datetime.from_string(self.date_start)
        date_end_utc = fields.Datetime.from_string(self.date_end)

        # Localize dates to operate with it correctly because shifts
        # are stored in local hours
        tz = timezone(self._context.get('tz') or self.env.user.tz or 'UTC')
        date_start = date_start_utc + tz.utcoffset(date_start_utc)
        date_end = date_end_utc + tz.utcoffset(date_end_utc)

        days = self.env['mrp.calendar.days'].search([
            ('day', '>=', date_start_utc.strftime('%Y-%m-%d')),
            ('day', '<=', date_end_utc.strftime('%Y-%m-%d')),
            ('holiday', '=', False)
        ], order='day')

        class context:
            date = date_start
            elapsed = date_end - date_start
            timewalker = date_start

        def travel_hours(start, end):
            if start != end:
                moment = datetime.combine(context.date, datetime.min.time()) + \
                         timedelta(seconds=start * 3600)
                if moment > context.timewalker:
                    context.elapsed -= moment - context.timewalker
                    context.timewalker = moment

                if end < start:
                    context.date += timedelta(days=1)
                moment = datetime.combine(context.date, datetime.min.time()) + \
                         timedelta(seconds=end * 3600)
                if context.timewalker < moment:
                    context.timewalker = moment

        for day in days:
            context.date = fields.Date.from_string(day.day)
            travel_hours(day.s1_start, day.s1_end)
            travel_hours(day.s2_start, day.s2_end)
            travel_hours(day.s3_start, day.s3_end)

        if date_end > context.timewalker:
            context.elapsed -= date_end - context.timewalker

        self.estimated_time = context.elapsed.total_seconds() / 3600

    @api.one
    def _recommended_time(self):
        fixed_time = 0
        variable_time = 0
        for ta in self.product_id.time_adviser:
            if ta.type == 'fixed':
                fixed_time += ta.time
            else:
                variable_time += ta.time
        self.recommended_time = (fixed_time + (self.product_qty *
                                               variable_time)) / 3600

    @api.multi
    def generate_order_and_archive(self):
        # Update production planning order line and recompute requirements
        self.active = False
        self.compute = False
        self.stock_available = True  # In archive, its'nt necessary
        self.production_planning.recompute_requirements()
        self.product_id.product_tmpl_id.compute_detailed_stock()

        data = {
            'product_id': self.product_id.id,
            'bom_id': self.bom_id.id,
            'product_qty': self.product_qty,
            'product_uom': self.product_id.uom_id.id,
            'routing_id': self.line_id.id,
            'date_planned': self.date_start,
            'date_end_planned': self.date_end,
            'time_planned': self.estimated_time,
            'user_id': self.env.user.id,
            'origin': _('Production planning order Nº %s') % (self.id),
            'notes': self.note
        }

        if self.product_id.categ_id.finished_dest_location_id:
            data['location_dest_id'] = \
                self.product_id.categ_id.finished_dest_location_id.id

        # Create production order and show it
        order = self.production_order.create(data)

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'res_id': order.id,
            'target': 'current',
            'context': self.env.context,
        }

    @api.model
    def create(self, vals):
        vals['production_planning'] = self.env.\
            ref('stock_available_ph.production_planning_1').id
        return super(models.Model, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('date_start', False) or vals.get('date_end', False):
            has_production_order = False
            for o in self:
                has_production_order = has_production_order or o.production_order

            if has_production_order:
                raise Warning(_('The dates cannot be changed, '
                                'there are an associated production order'))

        return super(models.Model, self).write(vals)

    @api.multi
    def show_materials_needed(self):
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'production.planning.orders',
            'view_type': 'form',
            'view_mode': 'form',
            'res_id': self.id,
            'target': 'new',
            'context': self.env.context,
        }

    @api.multi
    def save_order(self):
        self.production_planning.recompute_requirements()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def unlink(self):
        self.compute = False
        self.product_id.product_tmpl_id.compute_detailed_stock()
        return super(models.Model, self).unlink()

    @api.multi
    def cancel_order(self):
        self.unlink()


class ProductionPlanningMaterials(models.Model):
    _name = 'production.planning.materials'
    _description = 'Prevision of needed materials'
    _rec_name = 'product_id'

    product_id = fields.Many2one(string='Material',
                                 comodel_name='product.product')
    default_code = fields.Char(related='product_id.default_code',
                               readonly=True)
    qty_required = fields.Float(string='Quantity required', digits=(16,2))
    qty_vsc_available = fields.Float(string='Virtual stock conservative',
                                 digits=(16,2))
    qty_incoming = fields.Float(related='product_id.real_incoming_qty',
                                digits=(16,2), readonly=True)
    out_of_existences = fields.Float(related='product_id.out_of_existences',
                                     digits=(16,2), readonly=True)
    out_of_existences_dismissed = fields.Float(
        related='product_id.out_of_existences_dismissed', digits=(16,2),
        readonly=True)
    uom = fields.Char(string='Unit of measure')
    orders = fields.Many2many(string='Orders',
                              comodel_name='production.planning.orders',
                              relation='production_planning_ord_mat_rel',
                              ondelete='cascade')
    stock_status = fields.Selection([('ok', 'Available'),
                                     ('out', 'Out of stock'),
                                     ('incoming', 'Incoming'),
                                     ('no_stock', 'Not available')],
                                    string='Stock status', default='ok')
    production_planning = fields.Many2one(comodel_name='production.planning',
                                          readonly=True)


class ProductionPlanningOrders(models.Model):
    _inherit = 'production.planning.orders'

    materials = fields.Many2many(string='Orders',
                                 comodel_name='production.planning.materials',
                                 relation='production_planning_ord_mat_rel')


class ProductionPlanning(models.Model):
    _inherit = 'production.planning'

    orders = fields.One2many(string='Production planning orders',
                             comodel_name='production.planning.orders',
                             inverse_name='production_planning')
    materials = fields.One2many(string='Prevision of needed materials',
                                comodel_name='production.planning.materials',
                                inverse_name='production_planning')

    @api.one
    def recompute_requirements(self):
        # Save a list of affected materials
        affected_materials = [m.product_id for m in self.materials]

        self.materials.unlink()
        for order in self.orders:
            if order.compute:
                for line in order.bom_id.bom_line_ids:
                    material = self.materials.search([('product_id', '=',
                                                       line.product_id.id)])
                    if material:
                        material.write({
                            'qty_required': material.qty_required +
                                            (line.product_qty * order.product_qty),
                            'orders': [(4, order.id)],
                        })
                    else:
                        material = self.materials.create({
                            'product_id': line.product_id.id,
                            'qty_required': line.product_qty * order.product_qty,
                            'qty_vsc_available': line.product_id.virtual_conservative,
                            'uom': line.product_uom.name,
                            'orders': [(4, order.id)],
                            'production_planning': self.id
                        })

                    if material.product_id not in affected_materials:
                        affected_materials.append(material.product_id)

        # Check material level of availability
        for m in self.materials:
            if m.qty_vsc_available + m.out_of_existences + m.qty_incoming < \
                    m.qty_required:
                m.stock_status = 'no_stock'
            elif m.qty_vsc_available + m.out_of_existences + m.qty_incoming >= \
                    m.qty_required and \
                    m.qty_vsc_available + m.out_of_existences < m.qty_required:
                m.stock_status = 'incoming'
            elif m.qty_vsc_available + m.out_of_existences >= m.qty_required \
                    and m.qty_vsc_available < m.qty_required:
                m.stock_status = 'out'
            else:
                m.stock_status = 'ok'

        # Inherits worst stock status to orders
        for order in self.orders:
            order.stock_status = 'ok'
            for m in order.materials:
                if m.stock_status != 'ok' and \
                   order.stock_status != 'no_stock' and \
                   (
                    (order.stock_status == 'ok') or
                    (order.stock_status == 'out' and
                        m.stock_status not in ('ok', 'out')) or
                    (order.stock_status == 'incoming' and
                        m.stock_status == 'no_stock')
                   ):
                    order.stock_status = m.stock_status

        # Trigger stock calculations on affected materials
        for product_id in affected_materials:
            product_id.product_tmpl_id.compute_detailed_stock()

    @api.multi
    def write(self, vals):
        new_ctx_self = self.with_context(disable_notify_changes = True)
        result = super(ProductionPlanning, new_ctx_self).write(vals)
        self.recompute_requirements()

        # Trigger stock calculations on affected orders products
        for order in self.orders:
            order.product_id.product_tmpl_id.compute_detailed_stock()

        return result

    @api.multi
    def action_compute(self):
        self.recompute_requirements()
