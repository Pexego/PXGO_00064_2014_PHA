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
from openerp import models, fields, api, exceptions, _
from datetime import datetime


class CrmClaim(models.Model):

    _inherit = 'crm.claim'

    date_str = fields.Date('Date without hour', compute='_get_date_str', store=True)
    doc_attached = fields.Selection((('yes', 'YES'), ('no', 'NO')), 'Attached documentation')
    sample_attached = fields.Selection((('yes', 'YES'), ('no', 'NO')), 'Sample attached')
    quality_report = fields.Text('Quality report')
    quality_control_report = fields.Boolean('Quality control')
    quality_warranty_report = fields.Boolean('Warranty report')
    tech_dir_report = fields.Text('Technical direction report')
    tech_dir_conclusion = fields.Text('Technical direction conclusion')
    result_and_solution = fields.Text('Result and solution')
    action_taken = fields.Text('Action taken')
    economic_valuation = fields.Float('Economic valuation')
    general_dir_ver_and_auth = fields.Text('verification and authorization by general'
                                           ' management')
    products = fields.Char('Products', compute='_get_products', store=True)
    lots = fields.Char('Lots', compute='_get_lots', store=True)
    quantities = fields.Char('Quantities', compute='_get_quantities', store=True)

    @api.one
    @api.depends('date')
    def _get_date_str(self):
        self.date_str = datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S').date()

    @api.one
    @api.depends('claim_line_ids.product_id')
    def _get_products(self):
        self.products = ', '.join([x.product_id.name for x in self.claim_line_ids])

    @api.one
    @api.depends('claim_line_ids.prodlot_id')
    def _get_lots(self):
        self.lots = ', '.join([x.prodlot_id.name for x in self.claim_line_ids])

    @api.one
    @api.depends('claim_line_ids.product_returned_quantity')
    def _get_quantities(self):
        quantities_list = [str(x.product_returned_quantity) for x in self.claim_line_ids]
        self.quantities = ', '.join(quantities_list)
