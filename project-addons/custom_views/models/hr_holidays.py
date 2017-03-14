# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class HrHolidays(models.Model):
    _inherit = 'hr.holidays'
#    _rec_name = 'employee_id'

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

    @api.multi
    def name_get(self):
        res = []
        for rec in self:  # Why we need sudo() when we have access rights to hr.employee?
            res.append((rec.id, rec.sudo().employee_id.name))
        return res


class HrHolidaysManagement(models.TransientModel):
    _name = 'hr.holidays.management'
    _rec_name = 'holidays_status_id'

    holidays_status_id = fields.Many2one(
        comodel_name='hr.holidays.status',
        domain="[('limit', '=', False)]",
        string='Holidays status')
    current_holidays_status_id = fields.Many2one(
        comodel_name='hr.holidays.status',
        compute='_get_current_holidays_status',
        string='Current holidays status')
    remaining_days = fields.Integer(
        string='Remaining days to set',
        default=22)

    @api.one
    @api.depends('holidays_status_id')
    def _get_current_holidays_status(self):
        status_ids = self.env['hr.holidays.status'].search([('limit', '=', False)])
        self.current_holidays_status_id = status_ids and status_ids[0] or False
        if len(status_ids) > 1:
            raise Warning(_('There are more than one holidays status active'))

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
                        remaining_days = holiday.number_of_days
                        if remaining_days > leaves:
                            holiday.number_of_days_temp -= leaves
                        else:
                            holiday.number_of_days_temp = 0
                        leaves = leaves - remaining_days
        return True

    @api.multi
    def set_remaining_days(self):
        status_ids = self.env['hr.holidays.status'].search([('limit', '=', False)])
        if len(status_ids) != 1:
            raise Warning(_("The feature behind the field 'Remaining Legal Leaves' "
                            "can only be used when there is only one leave type "
                            "with the option 'Allow to Override Limit' unchecked. "
                            "(%s Found). Otherwise, the update is ambiguous as "
                            "we cannot decide on which leave type the update has "
                            "to be done. \nYou may prefer to use the classic menus "
                            "'Leave Requests' and 'Allocation Requests' located "
                            "in 'Human Resources \ Leaves' to manage the leave days "
                            "of the employees if the configuration does not allow "
                            "to use this field.") % (len(status_ids)))

        if not self.remaining_days or self.remaining_days < 1:
            raise Warning(_('You must specify the number of remaining days'))

        employees = self.env['hr.employee'].\
            search([('company_id', '=', self.env.user.company_id.id)])
        for employee in employees:
            employee.remaining_leaves = self.remaining_days
        return True