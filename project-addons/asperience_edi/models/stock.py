# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2015 Comunitea Servicios Tecnológicos All Rights Reserved
#    $Omar Castiñeira Saaevdra <omar@comunitea.com>$
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
import openerp.addons.decimal_precision as dp


class StockPackOperation(models.Model):

    _inherit = 'stock.pack.operation'

    sscc = fields.Char('SSCC')
    price_subtotal = fields.Float(
        compute='_get_subtotal', string="Subtotal",
        digits=dp.get_precision('Account'), readonly=True,
        store=True, multi=True)
    price_subtotal_net = fields.Float(
        compute='_get_subtotal', string="Net subtotal",
        digits=dp.get_precision('Account'), readonly=True,
        store=True, multi=True)
    price_total = fields.Float(
        compute='_get_subtotal', string="Total",
        digits=dp.get_precision('Account'), readonly=True,
        store=True, multi=True)

    @api.multi
    @api.depends('product_id', 'product_qty')
    def _get_subtotal(self):

        for op in self:
            # con parche solo hay 1 movimiento enlazado
            move = op.mapped('linked_move_operation_ids.move_id')
            if len(move) != 1:
                continue

            price_unit = 0.0
            price_unit_net = 0.0
            if move.procurement_id.sale_line_id:
                price_unit = move.procurement_id.sale_line_id.price_unit
                price_unit_net = (
                    move.procurement_id.sale_line_id.price_unit *
                    (1-(move.procurement_id.sale_line_id.discount or
                        0.0) / 100.0))
            else:
                continue

            op.price_subtotal = price_unit * op.product_qty
            op.price_subtotal_net = price_unit_net * op.product_qty
            taxes = move.procurement_id.sale_line_id.tax_id.compute_all(
                price_unit_net, op.product_qty, op.product_id,
                move.procurement_id.sale_line_id.order_id.partner_id)
            op.price_total = taxes['total_included']


class StockPicking(models.Model):

    _inherit = 'stock.picking'

    @api.model
    def _invoice_create_line(self, moves, journal_id, inv_type='out_invoice'):
        res = super(StockPicking, self)._invoice_create_line(
            moves, journal_id, inv_type)
        if self.env.context.get('split_invoice_lines', False):
            for invoice in self.env['account.invoice'].browse(res):
                for line in invoice.invoice_line:
                    if line.move_id.linked_move_operation_ids:
                        if len(line.move_id.linked_move_operation_ids) > 1:
                            for operation in \
                                    line.move_id.mapped(
                                    'linked_move_operation_ids.operation_id'):
                                line.copy({'quantity': operation.product_qty,
                                           'lot_id': operation.lot_id.id})
                            line.unlink()
                        else:
                            line.lot_id = line.move_id.linked_move_operation_ids.operation_id.lot_id.id
        return res


class StockInvoiceOnshipping(models.TransientModel):

    _inherit = 'stock.invoice.onshipping'

    split_invoice_lines = fields.Boolean()

    @api.multi
    def create_invoice(self):
        return super(
            StockInvoiceOnshipping,
            self.with_context(
                split_invoice_lines=self.split_invoice_lines)).create_invoice()
