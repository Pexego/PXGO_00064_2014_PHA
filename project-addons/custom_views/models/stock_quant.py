# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
#    Marcos Ybarra Mayor <marcos.ybarra@pharmadus.com>$
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
from openerp import models, fields, api, exceptions, _


class LotStateSelection(models.Model):
    _inherit = 'stock.quant'

    lot_state = fields.Selection(string='Lot state', related='lot_id.state')

    @api.multi
    def unlink(self):
        if self._context.get('nodelete', False):
            raise exceptions.Warning(_('Deletion aviod'),
                                     _('quants erasing is not allowed'))
        return super(LotStateSelection, self).unlink()
