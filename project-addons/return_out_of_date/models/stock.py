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
from openerp import models, api, fields, _


class StockMove(models.Model):

    _inherit = 'stock.move'

    @api.model
    def check_tracking_product(self, product, lot_id, location, location_dest):
        if not self.env.context.get('no_track', False):
            return super(StockMove, self).check_tracking_product(
                product, lot_id, location, location_dest)


class StockQuant(models.Model):

    _inherit = 'stock.quant'

    @api.model
    def _quants_get_order(self, location, product, quantity, domain=[],
                          orderby='in_date'):
        if self.env.context.get('search_quant_by_partner', False):
            partner_id = self.env.context['search_quant_by_partner']
            moves = self.env['stock.move'].search([('partner_id', 'child_of',
                                                    partner_id)])
            quant_ids = []
            for move in moves:
                quant_ids += list(move.quant_ids._ids)
            domain += [('id', 'in', quant_ids)]
        res = super(StockQuant, self)._quants_get_order(location, product,
                                                        quantity, domain,
                                                        orderby)
        domain_lot = [True for x in domain if x[0] == 'lot_id']
        lot_in_domain = len(domain_lot) and True or False
        if self.env.context.get('no_track', False) and not lot_in_domain:
            res = [(None, x[1]) for x in res]
        return res


class StockWarehouse(models.Model):

    _inherit = "stock.warehouse"

    out_of_date_type_id = fields.Many2one('stock.picking.type',
                                          'Out of date Type')

    @api.model
    def create(self, vals):
        seq_obj = self.env['ir.sequence']
        warehouse = super(StockWarehouse, self).create(vals)
        ood_loc = self.env['stock.location'].create({
            'name': 'Out of date',
            'location_id':
            self.env.ref('stock.stock_location_locations_partner').id,
            'usage': 'customer',
            'active': True
        })
        ood_seq = seq_obj.sudo().create(
            {'name': warehouse.name + _(' Sequence out of date'),
             'prefix': warehouse.code + '/OOD/', 'padding': 5})
        max_sequence = self.env['stock.picking.type'].search_read(
            [], ['sequence'], order='sequence desc')
        max_sequence = max_sequence and max_sequence[0]['sequence'] or 0
        ood_type_id = self.env['stock.picking.type'].create({
            'name': _('Out of date'),
            'warehouse_id': warehouse.id,
            'code': 'incoming',
            'sequence_id': ood_seq.id,
            'default_location_src_id':
            self.env.ref('stock.stock_location_customers').id,
            'default_location_dest_id': ood_loc.id,
            'sequence': max_sequence + 1})
        warehouse.write({'out_of_date_type_id': ood_type_id.id})
        return warehouse
