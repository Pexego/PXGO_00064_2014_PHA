# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Pharmadus I.T. Department. All Rights Reserved
#    $Óscar Salvador Páez <oscar.salvador@pharmadus.com>$
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as published
#    by the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program. If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp
from openerp.exceptions import Warning


class StockPrevisional(models.Model):
    _name = 'stock.previsional'
    _description = 'Previsional of stock needed to produce'

    name = fields.Char('Previsional')


class StockPrevisionalOrders(models.Model):
    _name = 'stock.previsional.orders'
    _description = 'Prevision of orders to produce'

    name = fields.Char(compute='_compound_name')
    date_start = fields.Datetime(string='Start date', default=fields.Date.today())
    date_end = fields.Datetime(string='End date', default=fields.Date.today())
    product_id = fields.Many2one(string='Final product',
                                 comodel_name='product.product',
                                 required=True)
    bom_id = fields.Many2one(string='Bills of materials',
                             comodel_name='mrp.bom',
                             required=True)
    line_id = fields.Many2one(string='Line',
                              comodel_name='mrp.routing',
                              required=True)
    product_qty = fields.Integer(string='Quantity to predict')
    previsional = fields.Many2one(comodel_name='stock.previsional',
                                  ondelete='cascade',
                                  readonly=True)
    compute = fields.Boolean(string='Compute', default=True)
    stock_available = fields.Boolean(string='Stock available', default=True)
    production_order = fields.Many2one(comodel_name='mrp.production',
                                       readonly=True)
    note = fields.Char(string='Note for production')
    active = fields.Boolean(default=True)

    @api.multi
    def _compound_name(self):
        for order in self:
            order.name =  u'{} ({:d}) ID: {:d}'.\
                format(order.product_id.name, order.product_qty, order.id)

    @api.onchange('product_id')
    def update_bom(self):
        bom_ids = self.env['mrp.bom'].search(
            [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)])
        self.bom_id = bom_ids[0] if bom_ids else False
        self.line_id = False
        return {'domain': {
            'bom_id': [('product_tmpl_id', '=', self.product_id.product_tmpl_id.id)],
            'line_id': [('id', 'in', self.product_id.routing_ids.ids)]}
        }

    @api.onchange('date_start')
    def check_date_end(self):
        if self.date_start > self.date_end:
            self.date_end = self.date_start

    @api.onchange('date_end')
    def check_date_start(self):
        if self.date_start > self.date_end:
            self.date_start = self.date_end

    @api.multi
    def generate_order_and_archive(self):
        # Update previsional order line and recompute requirements
        self.active = False
        self.compute = False
        self.stock_available = True  # In archive, its'nt necessary
        self.previsional.recompute_requirements()

        # Create production order and show it
        order = self.env['mrp.production'].create({
            'product_id': self.product_id.id,
            'bom_id': self.bom_id.id,
            'product_qty': self.product_qty,
            'product_uom': self.product_id.uom_id.id,
            'routing_id': self.line_id.id,
            'date_planned': self.date_start,
            'user_id': self.env.user.id,
            'origin': _('Previsional order Nº %s') % (self.id)
        })
        self.production_order = order
        if self.note:
            order.message_post(body=self.note)

        return {
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mrp.production',
            'res_id': order.id,
            'target': 'current',
            'context': self.env.context,
        }

    @api.model
    def create(self, vals):
        vals['previsional'] = self.env.\
            ref('stock_available.stock_previsional_1').id
        return super(models.Model, self).create(vals)

    @api.multi
    def write(self, vals):
        if vals.get('date_start', False) or vals.get('date_end', False):
            has_production_order = False
            for o in self:
                has_production_order = has_production_order or o.production_order

            if has_production_order:
                raise Warning(_('The dates cannot be changed, '
                                'there are an associated production order'))

        return super(models.Model, self).write(vals)


class StockPrevisionalOrderMaterials(models.Model):
    _name = 'stock.previsional.materials'
    _description = 'Prevision of needed materials'
    _rec_name = 'product_id'

    product_id = fields.Many2one(string='Material',
                                 comodel_name='product.product')
    default_code = fields.Char(related='product_id.default_code')
    qty_required = fields.Float(string='Quantity required', digits=(16,2))
    qty_vsc_available = fields.Float(string='Virtual stock conservative',
                                 digits=(16,2))
    uom = fields.Char(string='Unit of measure')
    orders = fields.Many2many(string='Orders',
                              comodel_name='stock.previsional.orders',
                              relation='stock_previsional_ord_mat_rel',
                              ondelete='cascade')
    previsional = fields.Many2one(comodel_name='stock.previsional',
                                  readonly=True)


class StockPrevisionalOrders(models.Model):
    _inherit = 'stock.previsional.orders'

    materials = fields.Many2many(string='Orders',
                                 comodel_name='stock.previsional.materials',
                                 relation='stock_previsional_ord_mat_rel')


class StockPrevisional(models.Model):
    _inherit = 'stock.previsional'

    orders = fields.One2many(string='Prevision of orders to produce',
                             comodel_name='stock.previsional.orders',
                             inverse_name='previsional')
    materials = fields.One2many(string='Prevision of needed materials',
                                comodel_name='stock.previsional.materials',
                                inverse_name='previsional')

    @api.one
    def recompute_requirements(self):
        self.materials.unlink()
        for order in self.orders:
            order.stock_available = True
            if order.compute:
                for line in order.bom_id.bom_line_ids:
                    material = self.materials.search([('product_id', '=',
                                                       line.product_id.id)])
                    if material:
                        material.write({
                            'qty_required': material.qty_required +
                                            (line.product_qty * order.product_qty),
                            'orders': [(4, order.id)],
                        })
                    else:
                        self.materials.create({
                            'product_id': line.product_id.id,
                            'qty_required': line.product_qty * order.product_qty,
                            'qty_vsc_available': line.product_id.virtual_conservative,
                            'uom': line.product_uom.name,
                            'orders': [(4, order.id)],
                            'previsional': self.id
                        })

        # Check availability of material
        for material in self.materials:
            if material.qty_required > material.qty_vsc_available:
                material.orders.write({'stock_available': False})

    @api.multi
    def write(self, vals):
        result = super(StockPrevisional, self).write(vals)
        self.recompute_requirements()
        return result
