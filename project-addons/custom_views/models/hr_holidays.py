# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'

    # Auxiliary field to make number_of_days_temp read only
    number_of_days_aux = fields.Float(readonly=True)

    @api.onchange('number_of_days_temp')
    def onchange_number_of_days(self):
        self.number_of_days_aux = self.number_of_days_temp

    @api.multi
    def write(self, vals):
        value = vals.get('number_of_days_aux',
                         vals.get('number_of_days_temp', False))
        vals['number_of_days_aux'] = value or self.number_of_days_temp
        return super(HrHolidays, self).write(vals)


class HrHolidaysManagement(models.TransientModel):
    _name = 'hr.holidays.management'
    _rec_name = 'holidays_status_id'

    holidays_status_id = fields.Many2one(comodel_name='hr.holidays.status',
                                         string='Holidays status')

    @api.multi
    def set_remaining_leaves_to_zero(self):
        if not self.holidays_status_id:
            raise Warning(_('You must choose a holiday status'))

        employees = self.env['hr.employee'].\
            search([('company_id', '=', self.env.user.company_id.id)])
        for employee in employees:
            leaves = employee.remaining_leaves
            if leaves > 0:
                holidays = self.env['hr.holidays'].search([
                    ('employee_id', '=', employee.id),
                    ('state', 'in', ['confirm', 'validate1', 'validate']),
                    ('holiday_status_id', '=', self.holidays_status_id.id),
                    ('type', '=', 'add')])
                for holiday in holidays:
                    if leaves > 0:
                        if holiday.number_of_days > leaves:
                            holiday.number_of_days = holiday.number_of_days - leaves
                        else:
                            holiday.number_of_days = 0
                        leaves = leaves - holiday.number_of_days
        return True