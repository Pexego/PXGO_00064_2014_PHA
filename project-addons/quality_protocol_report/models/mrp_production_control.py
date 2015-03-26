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

from openerp import models, fields


class MrpProductionControl(models.Model):

    _name = 'mrp.production.control'

    date = fields.Datetime('Hour')
    bag_maked = fields.Boolean('Maked')
    label = fields.Boolean('label')
    wrapped = fields.Boolean('wrapped')
    full_weight = fields.Float('Full')
    empty_weight = fields.Float('Empty')
    first = fields.Float('First production')
    middle = fields.Float('Middle production')
    last = fields.Float('Final production')
    initials = fields.Char("Initials")
    Workcenter_line_id = fields.Many2one('mrp.production.workcenter.line',
                                         'Workcenter line')
