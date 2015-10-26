# -*- coding: utf-8 -*-
##############################################################################
#
#        Copyright (C) 2014 Pharmadus All Rights Reserved
#        $Óscar Salvador <oscar.salvador@pharmadus.com>$
#
#        This program is free software: you can redistribute it and/or modify
#        it under the terms of the GNU Affero General Public License as published
#        by the Free Software Foundation, either version 3 of the License, or
#        (at your option) any later version.
#
#        This program is distributed in the hope that it will be useful,
#        but WITHOUT ANY WARRANTY; without even the implied warranty of
#        MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.    See the
#        GNU Affero General Public License for more details.
#
#        You should have received a copy of the GNU Affero General Public License
#        along with this program.    If not, see <http://www.gnu.org/licenses/>.
##############################################################################
#

from openerp import models, fields, api
from datetime import date, datetime


class product_drop(models.Model):
    _name = 'product.drop'
    _description = 'Internal use consumption'

    name = fields.Many2one(
        string='User',
        comodel_name='res.users',
        default=lambda r: r.env.user,
        ondelete='restrict',
        read=['base.group_user'],
        write=['base.group_erp_manager']
    )
    date = fields.Datetime(
        string='Date',
        default=datetime.now()
    )
    state = fields.Selection(
        string='State',
        selection=[('draft', 'Draft'),('done', 'Done')],
        default='draft'
    )


class product_drop_details(models.Model):
    _name = 'product.drop.details'
    _description = 'Consumed products'

    name = fields.Many2one(
        string='Product',
        comodel_name='product.product',
        ondelete='restrict'
    )
    product_qty = fields.Float(
        string='Quantity',
        default=1
    )
    lot_id = fields.Many2one(
        string='Lot',
        comodel_name='stock.production.lot'
    )
    move_id = fields.Many2one(
        string='Stock move',
        comodel_name='stock.move'
    )
    drop_id = fields.Many2one(
        string='Product drop',
        comodel_name='product.drop',
        ondelete='cascade'
    )

    @api.onchange('name', 'product_qty', 'lot_id')
    def on_change_name_qty(self):
        current_product = self.env.context.get('product_id')
        current_qty = self.env.context.get('product_qty')
        # Company's main stock location
#        location = self.env['stock.warehouse'].search(
#                [('company_id', '=', self.env.user.company_id.id)]
#            ).lot_stock_id.id
        # Physical Locations / CY01 / Existencias / Producto terminado
        location = self.env.ref('__export__.stock_location_22')

        # Search for lots of this product in main company stock.
        # Discards those that does not met minimum quantity needed and
        # are reserved
        lots_ids = self.env['stock.quant'].search([
                ('lot_id.product_id', '=', current_product),
                ('location_id.location_id', '=', location), # Parent's location
                ('reservation_id', '=', False),
                ('qty', '>=', current_qty)
            ]).mapped('lot_id.id')

        if lots_ids:
            if not (self.lot_id.id in lots_ids):
                self.lot_id = lots_ids[0]
        else:
            self.lot_id = False

        return {
            'domain': {
                'lot_id': [('id', 'in', lots_ids)]
            }
        }

    def _create_stock_move(self, lot, qty):
        company = self.env.user.company_id.id
        location = self.env['stock.warehouse'].search(
                [('company_id', '=', company)]
            ).lot_stock_id
        dest_id = self.env.ref('product_drop.consumption_for_internal_use_location')
        wh = self.env['stock.location'].get_warehouse(location)
        type_search_dict = [('code', '=', 'internal')]
        if wh:
            type_search_dict.append(('warehouse_id', '=', wh))
        picking_type = self.env['stock.picking.type'].search(
            type_search_dict)
        picking_vals = {
            'picking_type_id': picking_type.id,
            'partner_id': company,
            'date': date.today(),
            'origin': lot.name
        }
        picking_id = self.env['stock.picking'].create(picking_vals)

        move_dict = {
            'name': lot.product_id.name or '',
            'product_id': lot.product_id.id,
            'product_uom': lot.product_id.uom_id.id,
            'product_uos': lot.product_id.uos_id.id,
            'restrict_lot_id': lot.id,
            'product_uom_qty': qty,
            'date': date.today(),
            'date_expected': datetime.now(),
            'location_id': location.id,
            'location_dest_id': dest_id.id,
            'move_dest_id': False,
            'state': 'draft',
            'partner_id': company,
            'company_id': company,
            'picking_type_id': picking_type.id,
            'procurement_id': False,
            'origin': lot.name,
            'invoice_state': 'none',
            'picking_id': picking_id.id
        }
        new_move_id = self.env['stock.move'].create(move_dict)
        picking_id.action_assign() # Reserve items
        return new_move_id.id

    @api.model
    def create(self, vals):
        lot = self.env['stock.production.lot'].browse(vals['lot_id'])
        vals['move_id'] = self._create_stock_move(lot, vals['product_qty'])
        return super(product_drop_details, self).create(vals)

    @api.multi
    def write(self, vals):
        for detail in self:
            detail.move_id.picking_id.unlink()
            new_lot_id = vals['lot_id'] if vals.get('lot_id') else detail.lot_id
            new_product_qty = vals['product_qty'] if vals.get('product_qty') else detail.product_qty
            vals['move_id'] = detail._create_stock_move(new_lot_id, new_product_qty)
        return super(product_drop_details, self).write(vals)

    @api.multi
    def unlink(self):
        for detail in self:
            detail.move_id.picking_id.unlink()
        return super(product_drop_details, self).unlink()

    @api.model
    def unreserve_detail_id(self, detail_id):
        self.browse(detail_id).unlink()
        return True


class product_drop(models.Model):
    _inherit = 'product.drop'

    details_ids = fields.One2many(
        string='Consumed products',
        comodel_name='product.drop.details',
        inverse_name='drop_id',
    )

    @api.model
    def xmlrpc_create(self, user_id):
        res = self.sudo().create({'name': user_id})
        return res[0].id

    @api.multi
    def unlink(self):
        for drop in self:
            for detail in drop.details_ids:
                detail.move_id.picking_id.unlink()
        return super(product_drop, self).unlink()

    @api.multi
    def confirm_drop(self):
        for drop in self:
            for detail in drop.details_ids:
                detail.move_id.action_done()
            drop.state = 'done'

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'product.drop',
            'res_id': self.id,
            'target': 'current',
        }

    @api.model
    def confirm_drop_id(self, drop_id):
        self.browse(drop_id).confirm_drop()
        return True
