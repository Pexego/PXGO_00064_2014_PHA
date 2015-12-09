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
    show_sections = fields.Char('Show stage', compute='_get_show_sections')
    general_dir_ver_and_auth = fields.Text('verification and authorization by general'
                                           ' management')
    products = fields.Char('Products', compute='_get_products', store=True)
    lots = fields.Char('Lots', compute='_get_lots', store=True)
    quantities = fields.Char('Quantities', compute='_get_quantities', store=True)
    picking_id = fields.Many2one('stock.picking', 'Picking', domain=[('picking_type_code',
                                                                      '=', 'outgoing')])

    @api.one
    def _get_show_sections(self):
        self.show_sections = self.stage_id.show_sections

    @api.one
    @api.depends('date')
    def _get_date_str(self):
        self.date_str = datetime.strptime(self.date, '%Y-%m-%d %H:%M:%S').date()

    @api.one
    @api.depends('claim_line_ids.product_id')
    def _get_products(self):
        self.products = ', '.join([x.product_id.name for x in self.claim_line_ids
                                   if x.product_id])

    @api.one
    @api.depends('claim_line_ids.prodlot_id')
    def _get_lots(self):
        self.lots = ', '.join([x.prodlot_id.name for x in self.claim_line_ids if x.prodlot_id])

    @api.one
    @api.depends('claim_line_ids.product_returned_quantity')
    def _get_quantities(self):
        quantities_list = [str(x.product_returned_quantity) for x in self.claim_line_ids
                           if x.product_returned_quantity]
        self.quantities = ', '.join(quantities_list)

    @api.onchange('invoice_id', 'picking_id', 'warehouse_id', 'claim_type', 'date')
    def _onchange_invoice_warehouse_type_date(self):
        res = super(CrmClaim, self)._onchange_invoice_warehouse_type_date()
        claim_line_obj = self.env['claim.line']
        warehouse = self.warehouse_id
        if self.picking_id and self._context.get('create_lines', False):
            claim_lines = []
            for move in self.picking_id.move_lines:
                for packop in move.linked_move_operation_ids:
                    location_dest = claim_line_obj.get_destination_location(
                        packop.move_id.product_id, warehouse)
                    procurement = packop.move_id.procurement_id
                    warranty_return_address = claim_line_obj._warranty_return_address_values(
                        packop.move_id.product_id, self.company_id, warehouse)
                    warranty_return_address = warranty_return_address['warranty_return_partner']
                    line = {
                        'name': packop.move_id.name,
                        'claim_origine': "none",
                        'product_id': packop.move_id.product_id.id,
                        'product_returned_quantity': packop.operation_id.product_qty,
                        'unit_sale_price': procurement.sale_line_id.price_unit,
                        'location_dest_id': location_dest.id,
                        'warranty_return_partner': warranty_return_address,
                        'prodlot_id': packop.operation_id.lot_id.id,
                        'state': 'draft',
                    }
                    claim_lines.append((0, 0, line))
            value = self._convert_to_cache(
                {'claim_line_ids': claim_lines}, validate=False)
            self.update(value)
        return res


class CrmClaimLine(models.Model):

    _inherit = 'claim.line'

    def auto_set_warranty(self):
        return
