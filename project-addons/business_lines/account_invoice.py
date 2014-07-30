# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego Sistemas Informáticos All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@pexego.es>$
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
from datetime import date


class account_invoice(models.Model):
    _inherit = 'account.invoice'

    @api.multi
    def action_date_assign(self):
        """
            Se hereda la función debido al bug #1236
            ya que no se añade la fecha actual a la factura
            al validarla.
        """
        res = super(account_invoice, self).action_date_assign()
        for invoice in self:
            if not invoice.date_invoice:
                invoice.date_invoice = date.today()
        return res
