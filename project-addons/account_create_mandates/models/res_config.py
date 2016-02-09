# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from openerp import models, api
import time


class AccountConfigSettings(models.Model):
    _inherit = 'account.config.settings'

    @api.one
    def create_banking_mandates(self):
        company_ids = self.env['res.company'].search([])
        company_partner_ids = [c.partner_id.id for c in company_ids]
        partner_ids = self.env['res.partner'].\
            search([('company_id', '=', self.company_id.id),
                    ('id', 'not in', company_partner_ids),
                    ('bank_ids', '!=', False)])
        partner_with_bank_account_ids = [p.id for p in partner_ids]
        bank_ids = self.env['res.partner.bank'].\
            search([('partner_id', 'in', partner_with_bank_account_ids),
                    ('mandate_ids', '=', False)])

        current_date = time.strftime('%Y-%m-%d', time.localtime())

        banking_mandate = self.env['account.banking.mandate']
        for bank in bank_ids:
            banking_mandate.create({
                'company_id': bank.partner_id.company_id.id,
                'partner_bank_id': bank.id,
                'type': 'recurrent',
                'signature_date': current_date,
                'state': 'valid',
                'recurrent_sequence_type': 'recurring'
            })
        return self