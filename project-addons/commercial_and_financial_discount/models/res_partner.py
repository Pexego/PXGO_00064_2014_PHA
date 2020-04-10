# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com$
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
##############################################################################

from openerp import api, models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    commercial_discount = fields.Float(
        "Commercial discount (%)",
        help="If select this partner in sale order, discount will be added to order",
        default=0.0)
    financial_discount = fields.Float(
        "Financial discount (%)",
        help="If select this partner in sale order, discount will be added to order",
        default=0.0)

    @api.model
    def _commercial_fields(self):
        return super(ResPartner, self)._commercial_fields() + ['commercial_discount', 'financial_discount']
