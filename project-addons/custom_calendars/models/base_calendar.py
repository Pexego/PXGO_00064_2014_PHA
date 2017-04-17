# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api
from datetime import date, timedelta


class BaseCalendar(models.Model):
    _name = 'base.calendar'
    _description = 'Calendar'
    _rec_name = 'year'
    _order = 'year desc'

    year = fields.Integer('Year')


class BaseCalendarDays(models.Model):
    _name = 'base.calendar.days'
    _rec_name = 'day'
    _order = 'day'

    day = fields.Date('Day', readonly=True)
    weekday = fields.Selection([(1, 'monday'),
                                (2, 'tuesday'),
                                (3, 'wednesday'),
                                (4, 'thursday'),
                                (5, 'friday'),
                                (6, 'saturday'),
                                (7, 'sunday')], readonly=True)
    week = fields.Integer(readonly=True)
    month = fields.Selection([(1, 'january'),
                              (2, 'february'),
                              (3, 'march'),
                              (4, 'april'),
                              (5, 'may'),
                              (6, 'june'),
                              (7, 'july'),
                              (8, 'august'),
                              (9, 'september'),
                              (10, 'october'),
                              (11, 'november'),
                              (12, 'december')])
    year = fields.Many2one(comodel_name='base.calendar', ondelete='cascade')
    holiday = fields.Boolean('Holiday?', default=False)


class BaseCalendar(models.Model):
    _inherit = 'base.calendar'

    days = fields.One2many(comodel_name='base.calendar.days',
                           inverse_name='year')
    mrp_days = fields.One2many(comodel_name='mrp.calendar.days',
                               inverse_name='year')

    @api.model
    def create(self, vals):
        res = super(models.Model, self).create(vals)

        def perdelta(start, end, delta):
            curr = start
            while curr < end:
                yield curr
                curr += delta

        days = []
        for d in perdelta(date(res.year, 1, 1),
                          date(res.year + 1, 1, 1),
                          timedelta(days=1)):
            days.append((0, 0, {
                'day': d,
                'weekday': d.isoweekday(),
                'week': d.isocalendar()[1],
                'month': d.month
            }))
        res.write({'days': days})

        mrp_days = []
        for d in res.days.ids:
            mrp_days.append((0, 0, {'base_day': d}))
        res.write({'mrp_days': mrp_days})

        return res