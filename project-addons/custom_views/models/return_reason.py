# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ReturnReason(models.Model):
    _name = 'return.reason'
    _order = 'name'

    name = fields.Char(required=True)
    account_id = fields.Many2one(comodel_name='account.account', required=True)
