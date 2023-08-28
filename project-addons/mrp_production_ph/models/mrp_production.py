# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _, exceptions
import urllib
import unicodedata
from datetime import datetime, timedelta
from pytz import timezone
import openerp.addons.decimal_precision as dp


class MrpProductionStoreConsumption(models.TransientModel):
    _name = 'mrp.production.store.consumption'
    _order = 'order'

    production_id = fields.Many2one('mrp.production')
    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product')
    lot_id = fields.Many2one(comodel_name='stock.production.lot', string='Lot')
    quantity = fields.Float(digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one(comodel_name='product.uom', string='UoM')
    order = fields.Integer()


class MrpProductionQualityConsumption(models.TransientModel):
    _name = 'mrp.production.quality.consumption'
    _order = 'order'

    production_id = fields.Many2one('mrp.production')
    product_id = fields.Many2one(comodel_name='product.product',
                                 string='Product')
    lot_id = fields.Many2one(comodel_name='stock.production.lot', string='Lot')
    quantity = fields.Float(digits=dp.get_precision('Product Unit of Measure'))
    uom_id = fields.Many2one(comodel_name='product.uom', string='UoM')
    order = fields.Integer()


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_tmpl_id = fields.Many2one(comodel_name='product.template',
                                      related='product_id.product_tmpl_id',
                                      readonly=True)
    next_lot = fields.Char(compute='_next_lot', readonly=True)
    use_date = fields.Datetime(related='final_lot_id.use_date')
    duration_type = fields.Selection(selection=[
            ('exact', 'Exact'),
            ('end_month', 'End of month'),
            ('end_year', 'End of year')
        ], related='final_lot_id.duration_type')
    time_planned = fields.Float(compute='_time_planned', readonly=True)
    notes = fields.Text()
    store_consumption_ids = fields.One2many(
        comodel_name='mrp.production.store.consumption',
        inverse_name='production_id',
        compute='_compute_consumption',
        string='Store consumption')
    quality_consumption_ids = fields.One2many(
        comodel_name='mrp.production.quality.consumption',
        inverse_name='production_id',
        compute='_compute_consumption',
        string='Quality consumption')
    hoards_quants_reserved = fields.Boolean(compute='_hoards_quants_reserved')
    production_warning = fields.Char(compute='_production_warning',
                                     readonly=True)
    picking_weight = fields.Float(
        default=0.0,
        digits=dp.get_precision('Product Unit of Measure'))
    return_weight = fields.Float(
        digits=dp.get_precision('Product Unit of Measure'))
    tare = fields.Float(digits=dp.get_precision('Product Unit of Measure'))
    calculate_consumption_button_pressed = fields.Boolean(default=False)

    @api.multi
    def _hoards_quants_reserved(self):
        for production in self:
            hoard_ids = production.hoard_ids.filtered(
                lambda h: h.state in ('assigned', 'partially_available'))
            production.hoards_quants_reserved = True if hoard_ids else False

    @api.multi
    def _production_warning(self):
        for production_id in self:
            if production_id.routing_id.code[0:3] == 'REP':
                production_id.production_warning = \
                    self.env['ir.config_parameter'].\
                        get_param('reprocessing_route_warning')
            else:
                production_id.production_warning = \
                    production_id.product_id.production_warning

    def _compute_consumptions(self):
        consumptions = []
        # Gathering pickings
        for po in self.hoard_ids.sudo().filtered(lambda p: p.state == 'done').\
                mapped('pack_operation_ids'):
            idx = -1
            for i, obj in enumerate(consumptions):
                if obj['product_id'] == po.product_id.id and \
                        obj['lot_id'] == po.lot_id.id:
                    idx = i
            if idx > -1:
                consumptions[idx]['quantity'] += po.product_qty
            else:
                bom_line_id = self.bom_id.bom_line_ids.\
                    filtered(lambda r: r.product_id == po.product_id)
                consumptions.append({
                    'production_id': self.id,
                    'product_id': po.product_id.id,
                    'lot_id': po.lot_id.id,
                    'quantity': po.product_qty,
                    'uom_id': po.product_uom_id.id,
                    'order': bom_line_id.sequence if bom_line_id else 999
                 })

        # Return moves
        for m in self.move_lines2.sudo().filtered(
                lambda r: r.location_id.usage == 'internal' and
                          r.location_dest_id.usage == 'internal'):
            idx = -1
            for i, obj in enumerate(consumptions):
                if obj['product_id'] == m.product_id.id and \
                        obj['lot_id'] == (m.lot_ids[0].id if m.lot_ids
                                          else False):
                    idx = i
            if idx > -1:
                consumptions[idx]['quantity'] -= m.product_qty
            else:
                bom_line_id = self.bom_id.bom_line_ids.sudo().\
                    filtered(lambda r: r.product_id == m.product_id)
                consumptions.append({
                    'production_id': self.id,
                    'product_id': m.product_id.id,
                    'lot_id': m.lot_ids[0].id if m.lot_ids else False,
                    'quantity': -m.product_qty,
                    'uom_id': m.product_uom.id,
                    'order': bom_line_id.sequence if bom_line_id else 999
                })

        sc = self.env['mrp.production.store.consumption']
        sc.search([('production_id', '=', self.id)]).unlink()
        for c in consumptions:
            if c['quantity'] != 0:
                sc |= sc.create(c)

        # Return pickings
        for po in self.manual_return_pickings.sudo().\
                filtered(lambda p: p.state == 'done').\
                mapped('pack_operation_ids'):
            idx = -1
            for i, obj in enumerate(consumptions):
                if obj['product_id'] == po.product_id.id and \
                        obj['lot_id'] == po.lot_id.id:
                    idx = i
            sign = -1 if po.location_dest_id.usage == 'internal' else 1
            if idx > -1:
                consumptions[idx]['quantity'] += po.product_qty * sign
            else:
                bom_line_id = self.bom_id.bom_line_ids.sudo().\
                    filtered(lambda r: r.product_id == po.product_id)
                consumptions.append({
                    'production_id': self.id,
                    'product_id': po.product_id.id,
                    'lot_id': po.lot_id.id,
                    'quantity': po.product_qty * sign,
                    'uom_id': po.product_uom_id.id,
                    'order': bom_line_id.sequence if bom_line_id else 999
                })

        qc = self.env['mrp.production.quality.consumption']
        qc.search([('production_id', '=', self.id)]).unlink()
        for c in consumptions:
            if c['quantity'] != 0:
                qc |= qc.create(c)

        return sc, qc

    @api.one
    def _compute_consumption(self):
        trying = True
        attempts = 10
        while trying and attempts > 0:
            try:
                sc, qc = self._compute_consumptions()
                self.store_consumption_ids = sc
                self.quality_consumption_ids = qc
                trying = False
            except:
                self.env.cr.commit()
                attempts -= 1
                continue
        if attempts == 0:
            self.env.invalidate_all()
            self.store_consumption_ids = self.\
                env['mrp.production.store.consumption']
            self.quality_consumption_ids = self.\
                env['mrp.production.quality.consumption']

    @api.one
    def _next_lot(self):
        if self.product_id and self.product_id.sequence_id:
            sequence = self.product_id.sequence_id
        else:
            sequence = self.env.ref('stock.sequence_production_lots')

        if sequence:
            d = sequence._interpolation_dict()
            prefix = sequence.prefix and sequence.prefix % d or ''
            suffix = sequence.suffix and sequence.suffix % d or ''
            self.next_lot = prefix + '%%0%sd' % sequence.padding % \
                                     sequence.number_next_actual + suffix
        else:
            self.next_lot = False

    @api.multi
    def copy_from_lot(self):
        use_id = self.env['mrp.production.use.lot'].create({
            'production_id': self.id
        })
        wizard = self.env.ref('mrp_production_ph.mrp_production_use_lot_wizard')
        return {
            'name': _('Lot from which the use date and duration type are to be '
                      'copied'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production.use.lot',
            'views': [(wizard.id, 'form')],
            'view_id': wizard.id,
            'target': 'new',
            'res_id': use_id.id,
        }

    def _search_oldest_raw_material_lot(self):
        if self.bom_id.bom_line_ids:
            lowest_sequence = min(self.bom_id.\
                mapped('bom_line_ids.product_id.categ_id').\
                filtered(lambda c: c.analysis_sequence > 0).\
                mapped('analysis_sequence'))
            product_ids = self.bom_id.mapped('bom_line_ids.product_id').\
                filtered(lambda p: p.categ_id.analysis_sequence == lowest_sequence)
            lot_ids = self.hoard_ids.sudo().\
                mapped('move_lines.reserved_quant_ids').\
                filtered(lambda q: q.product_id in product_ids).\
                mapped('lot_id').sorted(key=lambda l: l.use_date)
            return lot_ids[0] if lot_ids else False
        else:
            return False

    """ Old code that calls wizard to choose one raw material lot
    @api.multi
    def add_suffix_from_lot(self):
        use_id = self.env['mrp.production.use.lot'].create({
            'production_id': self.id
        })
        wizard = self.env.\
            ref('mrp_production_ph.mrp_production_add_suffix_from_lot_wizard')
        return {
            'name': _('Lot from which the year and serial suffix are to be '
                      'copied'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production.use.lot',
            'views': [(wizard.id, 'form')],
            'view_id': wizard.id,
            'target': 'new',
            'res_id': use_id.id,
        }
    """
    @api.multi
    def add_suffix_from_lot(self):
        rm_lot_id = self._search_oldest_raw_material_lot()
        if rm_lot_id:
            suffix = rm_lot_id.name
            aPos = [pos for pos, char in enumerate(suffix) if char == '-']
            if len(aPos) > 1:
                final_lot_id = self.final_lot_id
                # Using sudo() to avoid mail warnings about modified lot names
                final_lot_id.sudo().write({
                    'name': final_lot_id.name + suffix[aPos[-2]:],
                    'use_date': rm_lot_id.use_date,
                    'duration_type': rm_lot_id.duration_type
                })
            else:
                raise exceptions.Warning(_('Lot error'),
                                         _('The selected lot do not have the '
                                           'expected suffix format.'))

    @api.multi
    def set_date_from_raw_material(self):
        lot_id = self._search_oldest_raw_material_lot()
        if lot_id:
            self.final_lot_id.write({
                'use_date': lot_id.use_date,
                'duration_type': lot_id.duration_type
            })

    @api.multi
    def action_call_update_display_url(self):
        def toASCII(text):
            return unicodedata.normalize('NFKD', text).encode('ascii', 'ignore')

        parameters = {
            'manufact_order': toASCII(self.name),
            'product': toASCII(self.product_id.name),
            'quantity': self.product_qty,
            'bill_of_materials': toASCII(self.bom_id.name),
            'routing': toASCII(self.routing_id.name),
            'final_lot': toASCII(self.final_lot_id.name),
            'target_location': toASCII(self.location_dest_id.name),
            'date_planned': self.date_planned,
            'date_end_planned': self.date_end_planned,
            'time_planned': self.time_planned
        }

        return {
            'type': 'ir.actions.act_url',
            'url': 'http://10.10.1.13/pantallas/producciones_odoo.php?' +
                urllib.urlencode(parameters),
            'target': 'new',
        }

    @api.one
    @api.depends('date_planned', 'date_end_planned')
    def _time_planned(self):
        if not (self.date_planned and self.date_end_planned):
            self.time_planned = 0
            return False

        date_start_utc = fields.Datetime.from_string(self.date_planned)
        date_end_utc = fields.Datetime.from_string(self.date_end_planned)

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

        self.time_planned = context.elapsed.total_seconds() / 3600

    @api.multi
    def product_id_change(self, product_id, product_qty=0):
        res = super(MrpProduction, self).product_id_change(product_id,
                                                           product_qty)
        if not res.get('domain', False):
            res['domain'] = {}
        product = self.env['product.product'].browse(product_id)
        if product.routing_ids:
            res['domain']['routing_id'] = [('product_ids', 'in', product.product_tmpl_id.id)]
        else:
            res['domain']['routing_id'] = [('wildcard_route', '=', True)]

        return res

    @api.multi
    def action_confirm(self):
        if self._context.get('from_wizard'):
            return super(MrpProduction, self).action_confirm()
        confirm_id = self.env['mrp.production.confirm'].create({
            'production_id': self.id,
            'product': self.product_id.name,
            'bom': self.bom_id.name,
            'routing': self.routing_id.name,
            'final_lot': self.final_lot_id.name,
            'next_lot': self.next_lot,
            'quantity': self.product_qty,
            'uom_id': self.product_uom.id
        })
        wizard = self.env.ref('mrp_production_ph.mrp_production_confirm_wizard')
        return {
            'name': _('Is going to start the production of'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production.confirm',
            'views': [(wizard.id, 'form')],
            'view_id': wizard.id,
            'target': 'new',
            'res_id': confirm_id.id,
        }

    @api.multi
    def action_stock_ldm_previsor(self):
        sa_id = self.env['stock.available'].create({
            'product_id': self.product_id.product_tmpl_id.id,
            'bom_id': self.bom_id.id,
            'product_qty': self.product_qty
        })
        sa_id.action_compute()

        view_id = self.env.ref('stock_available_ph.stock_available_form_view')
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'stock.available',
            'view_type': 'form',
            'view_mode': 'form',
            'view_id': view_id.id,
            'res_id': sa_id.id,
            'target': 'current',
            'context': self.env.context,
        }
