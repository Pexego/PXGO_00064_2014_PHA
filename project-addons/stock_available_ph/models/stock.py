# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields, api
import openerp.addons.decimal_precision as dp


class StockAvailable(models.TransientModel):
    _name = 'stock.available'
    _description = 'Available stock for bill of materials'
    _rec_name = 'product_id'

    product_id = fields.Many2one(string='Product',
                                 comodel_name='product.template')
    bom_id = fields.Many2one(string='Bills of materials',
                             comodel_name='mrp.bom',
                             domain="[('product_tmpl_id', '=', product_id)]")
    product_qty = fields.Integer(string='Quantity to calculate')

    @api.onchange('product_id')
    def update_bom(self):
        bom_ids = self.env['mrp.bom'].search(
            [('product_tmpl_id', '=', self.product_id.id)])
        self.bom_id = bom_ids[0] if bom_ids else False


class StockAvailableDetails(models.TransientModel):
    _name = 'stock.available.details'
    _description = 'Available stock for bill of materials lines'
    _rec_name = 'product_id'

    product_id = fields.Many2one(string='Product', comodel_name='product.product')
    default_code = fields.Char(string='Internal Reference')
    qty_required = fields.Float(string='Quantity required', digits=(16,2))
    qty_vsc_available = fields.Float(string='Virtual stock conservative',
                                 digits=(16,2))
    out_of_existences = fields.Float(string='Out of existences', digits=(16,2))
    out_of_existences_dismissed = fields.Float(string='Out of existences dismissed',
                                               digits=(16,2))
    qty_incoming = fields.Float(string='Incoming', digits=(16,2))
    uom = fields.Char(string='Unit of measure')
    bom_stock = fields.Many2one(comodel_name='stock.available', readonly=True)
    stock_status = fields.Selection([('ok', 'Available'),
                                     ('out', 'Out of stock'),
                                     ('incoming', 'Incoming'),
                                     ('no_stock', 'Not available')],
                                    string='Stock status', default='ok')
    bom_member = fields.Boolean(default=False)


class StockAvailable(models.TransientModel):
    _inherit = 'stock.available'

    bom_lines = fields.One2many(string='Bill of materials details',
                                comodel_name='stock.available.details',
                                inverse_name='bom_stock')

    @api.one
    def action_compute(self):
        self.bom_lines.unlink()
        for line in self.bom_id.bom_line_ids:
            qty_required = line.product_qty * self.product_qty
            qty_vsc_available = line.product_id.virtual_conservative
            out_of_existences = line.product_id.out_of_existences
            out_of_existences_dismissed = \
                line.product_id.out_of_existences_dismissed
            qty_incoming = line.product_id.real_incoming_qty

            # Check material level of availability
            if qty_vsc_available + out_of_existences + qty_incoming < qty_required:
                stock_status = 'no_stock'
            elif qty_vsc_available + out_of_existences + qty_incoming >= \
                    qty_required and \
                    qty_vsc_available + out_of_existences < qty_required:
                stock_status = 'incoming'
            elif qty_vsc_available + out_of_existences >= qty_required and \
                    qty_vsc_available < qty_required:
                stock_status = 'out'
            else:
                stock_status = 'ok'

            self.bom_lines.create({
                'product_id': line.product_id.id,
                'default_code': line.product_id.default_code,
                'qty_required': qty_required,
                'qty_vsc_available': qty_vsc_available,
                'out_of_existences': out_of_existences,
                'out_of_existences_dismissed': out_of_existences_dismissed,
                'qty_incoming': qty_incoming,
                'uom': line.product_uom.name,
                'bom_stock': self.id,
                'stock_status': stock_status,
                'bom_member': line.product_id.bom_member
            })
        return self


class StockWarehouseOrderpoint(models.Model):
    _inherit = 'stock.warehouse.orderpoint'

    product_min_action_qty = fields.Float(string='Minimum action quantity',
                                          default=0.0)


class StockQuant(models.Model):
    _inherit = 'stock.quant'

    reservation_picking_id = fields.Many2one(comodel_name='stock.picking',
                                             related='reservation_id.picking_id',
                                             readonly=True)
