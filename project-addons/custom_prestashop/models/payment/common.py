# -*- coding: utf-8 -*-
# © 2021 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import fields, models


class PaymentMethod(models.Model):
    _inherit = "payment.method"

    payment_mode_id = fields.Many2one("payment.mode", "Payment mode")
