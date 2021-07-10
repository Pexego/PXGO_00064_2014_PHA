# -*- coding: utf-8 -*-
# © 2021 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    can_reset = fields.Boolean(compute='_get_can_reset')

    @api.multi
    def _get_can_reset(self):
        """User can reset a leave request if it is its own leave request or if
        he is an Hr User. """
        if self.env.user in self.env.ref('base.group_hr_user').users:
            self.can_reset = True
        else:
            for holiday in self:
                holiday.can_reset = holiday.employee_id and \
                                    holiday.employee_id.user_id and \
                                    holiday.employee_id.user_id == self.env.user
