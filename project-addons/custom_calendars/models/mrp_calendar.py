# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class MRPCalendarDays(models.Model):
    _name = 'mrp.calendar.days'
    _inherits = {'base.calendar.days': 'base_day'}

    year = fields.Many2one(comodel_name='base.calendar')
    base_day = fields.Many2one(comodel_name='base.calendar.days',
                               required=True,
                               ondelete='cascade')
    s1_start = fields.Float('Shift 1 start', default=False)
    s1_end = fields.Float('Shift 1 end', default=False)
    s2_start = fields.Float('Shift 2 start', default=False)
    s2_end = fields.Float('Shift 2 end', default=False)
    s3_start = fields.Float('Shift 3 start', default=False)
    s3_end = fields.Float('Shift 3 end', default=False)
