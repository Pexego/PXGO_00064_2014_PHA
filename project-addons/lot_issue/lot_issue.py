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
from openerp import models, fields, api


class LotIssue(models.Model):

    _name = 'stock.production.lot.issue'
    _inherit = ['mail.thread', 'ir.needaction_mixin']

    @api.one
    def _get_user(self):
        self.user_id = self.env.user.id

    name = fields.Char('Name', size=64, required=True)
    description = fields.Text('Description')
    date = fields.Date('Date', required=True,
                       default=fields.Date.context_today)
    user_id = fields.Many2one('res.users', 'User', default=_get_user,
                              required=True)
    lot_id = fields.Many2one('stock.production.lot', 'Lot', required=True)
    product_id = fields.Many2one('product.product', 'Product',
                                 related='lot_id.product_id', readonly=True)


class StockProductionLot(models.Model):

    _inherit = 'stock.production.lot'

    @api.one
    def _get_issue_count(self):
        self.issue_count = len(self.issue_ids)

    issue_ids = fields.One2many('stock.production.lot.issue', 'lot_id',
                                'Issues')
    issue_count = fields.Integer('Issue count', compute=_get_issue_count)
