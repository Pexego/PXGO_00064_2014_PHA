# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, _
from openerp.exceptions import Warning


class MrpRouting(models.Model):
    _inherit = 'mrp.routing'

    finished_dest_location_id = fields.Many2one('stock.location',
                                                'Finished products location')


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    @api.one
    @api.onchange('routing_id')
    def onchange_routing_id(self):
        if self.routing_id.finished_dest_location_id:
            self.location_dest_id = self.routing_id.finished_dest_location_id

    @api.multi
    def action_confirm(self):
        for prod in self:
            if len(prod.location_dest_id.child_ids):
                raise Warning(_('Location Error'), _('Location %s has child locations. \
The movements should be at an end location') % prod.location_dest_id.name)
        return super(MrpProduction, self).action_confirm()
