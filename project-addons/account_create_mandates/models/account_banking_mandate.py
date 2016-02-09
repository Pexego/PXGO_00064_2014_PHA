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


class AccountBankingMandate(models.Model):
    _inherit = 'account.banking.mandate'

    @api.one
    def create_mandates(self):
        partners_banks = self.env['res.partner.bank'].\
            search([('company_id', '=', self.company_id.id)])

        current_date = time.strftime('%Y-%m-%d', time.localtime())

        for bank in partners_banks:
            if not len(bank.mandate_ids):
                self.create({
                    'company_id': self.company_id.id,
                    'partner_bank_id': bank.bank.id,
                    'type': 'recurrent',
                    'signature_date': current_date,
                    'state': 'valid',
                    'recurrent_sequence_type': 'recurring'
                })
        return True