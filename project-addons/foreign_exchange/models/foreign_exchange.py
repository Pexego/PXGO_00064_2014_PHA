# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
import datetime


class ForeignExchange(models.TransientModel):
    _name = 'foreign.exchange'
    _description = 'Foreign exchange'

    date = fields.Date(default=lambda self: fields.Date.today())
    date_adopted = fields.Datetime(string='Date adopted')
    source_currency = fields.Many2one(comodel_name='res.currency',
                         string='Source currency',
                         default=lambda r: r.env.user.company_id.currency_id.id)
    destination_currency = fields.Many2one(comodel_name='res.currency',
                                     string='Destination currency',
                                     default=lambda r: r.env.ref('base.USD').id)
    rate = fields.Float()
    money = fields.Float(default=1)
    result = fields.Float()
    account_move = fields.Many2one(comodel_name='account.move', default=0)
    wizard = fields.Boolean(default=False)

    @api.onchange('date',
                  'source_currency',
                  'destination_currency',
                  'money')
    def check_exchange_rate(self):
        company_currency = self.env.user.company_id.currency_id
        if self.date and (self.source_currency == company_currency or
                          self.destination_currency == company_currency):
            if self.source_currency == company_currency:
                target_currency = self.destination_currency
                inverse_conversion = False
            else:
                target_currency = self.source_currency
                inverse_conversion = True

            date_limit = fields.Date.to_string(
                fields.Date.from_string(self.date) + datetime.timedelta(days=1))
            rates = target_currency.rate_ids.\
                filtered(lambda r: r.name < date_limit).\
                sorted(key=lambda r: r.name, reverse=True)

            if rates:
                self.rate = 1 / rates[0].rate if inverse_conversion else \
                    rates[0].rate
                self.date_adopted = rates[0].name
            else:
                self.rate = 0
                self.date_adopted = False
        else:
            self.rate = 0
            self.date_adopted = False

        self.result = self.money * self.rate

    @api.model
    def create(self, vals):
        res = super(ForeignExchange, self).create(vals)
        res.check_exchange_rate()
        return res

    @api.multi
    def compute_exchange_rate(self):
        self.ensure_one()

        self.check_exchange_rate()

        company_currency = self.env.user.company_id.currency_id
        if self.source_currency == company_currency:
            for line in self.account_move.line_id:
                line.currency_id = self.destination_currency
                line.amount_currency = (line.debit - line.credit) * self.rate
        else:
            for line in self.account_move.line_id:
                line.currency_id = self.source_currency
                if line.amount_currency > 0:
                    line.debit = line.amount_currency * self.rate
                    line.credit = 0
                else:
                    line.debit = 0
                    line.credit = line.amount_currency * self.rate * -1

        return self.account_move

    @api.multi
    def swap(self):
        self.ensure_one()

        sc = self.source_currency
        self.source_currency = self.destination_currency
        self.destination_currency = sc
        self.check_exchange_rate()

        return {
            'context': self.env.context,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'foreign.exchange',
            'res_id': self.id,
            'view_id': False,
            'type': 'ir.actions.act_window',
            'name': _('Foreign exchange'),
            'target': 'new',
        }
