# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning
import datetime, time


class CalendarWizard(models.TransientModel):
    _name = 'calendar.wizard'
    _description = 'Calendar wizard'
    _rec_name = 'year'

    year = fields.Integer('Year', default=lambda self: self._get_default_year())
    day_begin = fields.Date('First day',
                            default=lambda self: self._get_default_day_begin())
    day_end = fields.Date('Last day',
                          default=lambda self: self._get_default_day_end())
    monday = fields.Boolean('Monday', default=True)
    tuesday = fields.Boolean('Tuesday', default=True)
    wednesday = fields.Boolean('Wednesday', default=True)
    thursday = fields.Boolean('Thursday', default=True)
    friday = fields.Boolean('Friday', default=True)
    saturday = fields.Boolean('Saturday', default=False)
    sunday = fields.Boolean('Sunday', default=False)
    s1_start = fields.Float('Shift 1 start', default=False)
    s1_end = fields.Float('Shift 1 end', default=False)
    s2_start = fields.Float('Shift 2 start', default=False)
    s2_end = fields.Float('Shift 2 end', default=False)
    s3_start = fields.Float('Shift 3 start', default=False)
    s3_end = fields.Float('Shift 3 end', default=False)

    @api.model
    def _get_default_year(self):
        cal = self.env['base.calendar'].search([], order='year desc', limit=1)
        if self.env.context.get('new_calendar', False):
            return cal.year + 1 if cal else datetime.date.today().year
        else:
            return cal.year if cal else datetime.date.today().year

    @api.model
    def _get_default_day_begin(self):
        return datetime.date(self._get_default_year(), 1, 1)

    @api.model
    def _get_default_day_end(self):
        return datetime.date(self._get_default_year(), 12, 31)


class CalendarWizardHolidays(models.TransientModel):
    _name = 'calendar.wizard.holidays'
    _rec_name = 'day'
    _order = 'day'

    wizard = fields.Many2one(comodel_name='calendar.wizard')
    day = fields.Date('Day', default=lambda self: self._get_first_day_of_year())

    @api.model
    def _get_first_day_of_year(self):
        year = self.env.context.get('year', self.wizard._get_default_year())
        return datetime.date(year, 1, 1)


class CalendarWizard(models.TransientModel):
    _inherit = 'calendar.wizard'

    holidays = fields.One2many(comodel_name='calendar.wizard.holidays',
                               inverse_name='wizard')

    @api.multi
    def create_calendar(self):
        if 2016 < self.year < 2100:
            calendar = self.env['base.calendar']
            if calendar.search([('year', '=', self.year)]):
                raise Warning(
                    _(u'¡Year {:d} has already been created!').format(self.year))
            else:
                calendar.create({'year': self.year})
                return {
                    'type': 'ir.actions.client',
                    'tag': 'reload',
                }
        else:
            raise Warning(_(u'Year {:d} out of range...').format(self.year))

    @api.multi
    def set_holidays(self):
        if self.holidays:
            bad_days = ''
            cal_days = self.env['mrp.calendar.days']
            for h in self.holidays:
                d = cal_days.search([('day', '=', h.day)])
                if d:
                    d.write({
                        'holiday':  True,
                        's1_start': False,
                        's1_end':   False,
                        's2_start': False,
                        's2_end':   False,
                        's3_start': False,
                        's3_end':   False
                    })
                else:
                    bad_day = time.strptime(h.day,'%Y-%m-%d')
                    bad_days += time.strftime('%d-%m-%Y', bad_day) + ', '
            if bad_days > '':
                raise Warning(_(u'Holidays {}can not be established because '
                                u'there is no corresponding calendar ...')
                              .format(bad_days))
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }

    @api.multi
    def set_fixed_shifts(self):
        weekdays = ()
        weekdays += (1,) if self.monday else ()
        weekdays += (2,) if self.tuesday else ()
        weekdays += (3,) if self.wednesday else ()
        weekdays += (4,) if self.thursday else ()
        weekdays += (5,) if self.friday else ()
        weekdays += (6,) if self.saturday else ()
        weekdays += (7,) if self.sunday else ()

        self.env['mrp.calendar.days'].search([
            ('day', '>=', self.day_begin),
            ('day', '<=', self.day_end),
            ('weekday', 'in', weekdays),
            ('holiday', '=', False)
        ]).write({
            's1_start': self.s1_start,
            's1_end':   self.s1_end,
            's2_start': self.s2_start,
            's2_end':   self.s2_end,
            's3_start': self.s3_start,
            's3_end':   self.s3_end
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
