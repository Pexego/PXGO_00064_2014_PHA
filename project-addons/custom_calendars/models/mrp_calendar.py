# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning


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

    def _check_shifts(self, vals):
        s1_start = vals.get('s1_start', self.s1_start)
        s1_end   = vals.get('s1_end',   self.s1_end)
        s2_start = vals.get('s2_start', self.s2_start)
        s2_end   = vals.get('s2_end',   self.s2_end)
        s3_start = vals.get('s3_start', self.s3_start)
        s3_end   = vals.get('s3_end',   self.s3_end)
        bad_shift = False

        if ((bool(s1_start) or bool(s1_end)) and (s1_start == s1_end)):
            bad_shift = 1
        elif ((bool(s2_start) or bool(s2_end)) and (s2_start == s2_end)):
            bad_shift = 2
        elif ((bool(s3_start) or bool(s3_end)) and (s3_start == s3_end)):
            bad_shift = 3

        if bad_shift:
            raise Warning(_(u'There is no time lapse between start and end of '
                            u'shift {:d}').format(bad_shift))
        return True

    @api.model
    def create(self, vals):
        if self._check_shifts(vals):
            return super(MRPCalendarDays, self).create(vals)
        else:
            return False

    @api.multi
    def write(self, vals):
        if self and self[0]._check_shifts(vals):
            if vals.get('holiday', False):
                vals['s1_start'] = False
                vals['s1_end']   = False
                vals['s2_start'] = False
                vals['s2_end']   = False
                vals['s3_start'] = False
                vals['s3_end']   = False
            return super(MRPCalendarDays, self).write(vals)
        else:
            return False
