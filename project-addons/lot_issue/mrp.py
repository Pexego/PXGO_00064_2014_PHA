# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Pexego All Rights Reserved
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
from openerp import models, api, fields
import ast


class MrpProduction(models.Model):

    _inherit = 'mrp.production'

    @api.one
    def _get_issue_count(self):
        self.issue_count = len(self.final_lot_id.issue_ids)

    issue_count = fields.Integer('Issue count', compute=_get_issue_count)

    @api.multi
    def create_issue(self):
        if not self.final_lot_id:
            return
        action = self.env.ref('lot_issue.action_issue2')
        if not action:
            return
        action = action.read()[0]
        context = action['context'].replace("active_id", "'active_id'")
        context = ast.literal_eval(context)
        context['search_default_lot_id'] = self.final_lot_id.id
        context['default_lot_id'] = self.final_lot_id.id
        context['default_user_id'] = self.env.user.id
        action['context'] = str(context)
        return action
