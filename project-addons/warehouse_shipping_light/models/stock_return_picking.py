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
import re


class StockReturnPicking(models.TransientModel):
    _inherit = 'stock.return.picking'

    @api.multi
    def create_returns(self):
        # Save context before...
        model = self.env.context.get('active_model')
        picking = self.env.context.get('active_id')

        # Revert transfer
        res = super(StockReturnPicking, self).create_returns()

        # Pass selected invoicing policy
        domain = res.get('domain')
        new_picking = re.findall(r'\d+', domain)
        if len(new_picking):
            new_picking = self.env['stock.picking'].browse(int(new_picking[0]))
            new_picking.invoice_state = self.invoice_state

        # Remove expedition
        if model == 'stock.picking' and picking:
            picking = self.env['stock.picking'].browse(picking)
            if picking and picking.expedition_id:
                picking.expedition_id.unlink()

        return res
