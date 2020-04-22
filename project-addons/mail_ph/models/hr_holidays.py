# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api

class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    @api.multi
    def holidays_validate(self):
        res = super(HrHolidays, self).holidays_validate()
        for holiday_id in self:
            template_id = self.env.ref('mail_ph.hr_holidays_mail_template')
            template_id.send_mail(holiday_id.id, force_send=True)
        return res

    @api.multi
    def holidays_refuse(self):
        res = super(HrHolidays, self).holidays_refuse()
        for holiday_id in self:
            template_id = self.env.ref('mail_ph.hr_holidays_refuse_mail_template')
            template_id.send_mail(holiday_id.id, force_send=True)
        return res