# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api
import urllib, unicodedata
from datetime import datetime, timedelta
from pytz import timezone

class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    product_tmpl_id = fields.Many2one(comodel_name='product.template',
                                      related='product_id.product_tmpl_id')
    next_lot = fields.Char(compute='_next_lot', readonly=True)
    time_planned = fields.Float(compute='_time_planned', readonly=True)

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