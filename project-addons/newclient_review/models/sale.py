# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Marcos Ybarra <marcos.ybarra@pharmadus.com>$
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
from openerp.exceptions import Warning
from openerp.tools.translate import _


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def action_button_confirm(self):
        # If one client data is not confirmed, sale(s) can't be done
        for sale in self:
            if (not sale.partner_id.confirmed):
                #Show message and rollback
                raise Warning(_('Client without review. A manager must review '
                                'data to confirm it before confirm order, you '
                                'can "Save" this order to confirm later.'))

        # Everything right, call original method
        return super(SaleOrder, self).action_button_confirm()
