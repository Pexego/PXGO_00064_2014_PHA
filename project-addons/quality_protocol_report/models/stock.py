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
from openerp import models, fields, api, exceptions, _


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    response_ids = fields.One2many('survey.user_input', 'lot_id', 'Responses')


class StockMove(models.Model):

    _inherit = "stock.move"

    workcenter_id = fields.Many2one('mrp.workcenter', 'Workcenter')
    checked_disp = fields.Boolean('Checked availability')


class StockPackOperation(models.Model):

    _inherit = 'stock.pack.operation'

    served_qty = fields.Float('Served qty',
                              help="Quality system field, no data")
    returned_qty = fields.Float('Returned qty', help="""Qty. of move that will
                                be returned on produce""")
    initials = fields.Char('Initials')
    initials_return = fields.Char('Initials')
    acceptance_date = fields.Date('Acceptance date', readonly=True,
                                  related='lot_id.acceptance_date')
