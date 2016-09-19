# -*- coding: utf-8 -*-
###############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2016 Pharmadus. All Rights Reserved
#    $Oscar Salvador <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################

from openerp import models, fields, api


class AccountInvoice(models.Model):
    _inherit='account.invoice'

    picking_ids = fields.One2many('stock.picking',
                                  compute='_compute_picking_ids')

    @api.one
    def _compute_picking_ids(self):
        origin = self.origin
        if origin:
            origin = origin.replace(' ', '')
            self.picking_ids = self.env['stock.picking']\
                .search([('name', 'in', origin.split())])
        else:
            self.picking_ids = False