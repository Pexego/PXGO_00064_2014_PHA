# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _


class AccountMove(models.Model):
    _inherit = 'account.move'

    @api.multi
    def compute_exchange_rate(self):
        wizard = self.env['foreign.exchange'].create({
            'date': self.date if self.date else fields.Date.today(),
            'source_currency': self.env.user.company_id.currency_id.id,
            'wizard': True,
        })

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'foreign.exchange',
            'res_id': wizard.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('Foreign exchange'),
            'target': 'new',
        }