# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class AccountMoveLine(models.Model):
    _inherit = 'account.move.line'

    partner_parent_category_id = fields.Many2one(
        comodel_name='res.partner.category',
        compute='_get_parent_category')
    payment_mode_bank_id = fields.Many2one(related='payment_mode_id.bank_id')

    @api.one
    def _get_parent_category(self):
        c = self.partner_id.category_id
        if c and c.parent_id:
            self.partner_parent_category_id = c.parent_id
        elif c:
            self.partner_parent_category_id = c