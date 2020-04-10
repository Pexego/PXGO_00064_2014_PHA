# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    over_due_first_notice_days = fields.Float()
    over_due_second_notice_days = fields.Float()
    over_due_third_notice_days = fields.Float()

    lot_alert_date_months_ahead = fields.Float()
    lot_use_date_months_ahead = fields.Float()