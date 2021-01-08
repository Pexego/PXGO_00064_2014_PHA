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


class StockPackOperationSscc(models.Model):

    _name = "stock.pack.operation.sscc"

    name = fields.Char()
    type = fields.Selection((("1", "Palet"), ("2", "Complete"), ("3", "package")))
    parent = fields.Many2one("stock.pack.operation.sscc")
    operation_ids = fields.Many2many(
        "stock.pack.operation", "operation_sscc_rel", "sscc_id", "operation_id"
    )
    child_ids = fields.One2many("stock.pack.operation.sscc", "parent")


class StockPackOperation(models.Model):

    _inherit = "stock.pack.operation"

    sscc_ids = fields.Many2many(
        "stock.pack.operation.sscc", "operation_sscc_rel", "operation_id", "sscc_id"
    )

    @api.multi
    def get_package_qty(self, type, move_id=False):
        """
        Se calcula la cantidad que va dentro de un bulto.
        """
        if type == "1":
            return sum([x.qty for x in self.linked_move_operation_ids])
        elif type == "2":
            return self.product_id.box_elements
        else:
            if move_id:
                qty = sum([x.qty for x in self.linked_move_operation_ids if x.move_id == move_id])
            else:
                qty = sum([x.qty for x in self.linked_move_operation_ids])
            return qty - (
                self.product_id.box_elements * self.complete
            )


class StockMove(models.Model):

    _inherit = "stock.move"

    price_subtotal_gross = fields.Float(
        compute="_get_total",
        string="Subtotal gross",
        digits=dp.get_precision("Account"),
        readonly=True,
        store=True,
        multi=True,
    )
    price_total = fields.Float(
        compute="_get_total",
        string="Total",
        digits=dp.get_precision("Account"),
        readonly=True,
        store=True,
        multi=True,
    )

    @api.multi
    @api.depends("product_id", "product_uom_qty", "procurement_id.sale_line_id")
    def _get_total(self):

        for move in self:
            price_unit = 0.0
            price_unit_net = 0.0
            if move.procurement_id.sale_line_id:
                price_unit = move.procurement_id.sale_line_id.price_unit
                price_unit_net = move.procurement_id.sale_line_id.price_unit * (
                    1 - (move.procurement_id.sale_line_id.discount or 0.0) / 100.0
                )
            else:
                continue

            move.price_subtotal_gross = price_unit * move.product_uom_qty
            taxes = move.procurement_id.sale_line_id.tax_id.compute_all(
                price_unit_net,
                move.product_uom_qty,
                move.product_id,
                move.procurement_id.sale_line_id.order_id.partner_id,
            )
            move.price_total = taxes["total_included"]


class StockPicking(models.Model):
    _inherit = "stock.picking"

    channel_name = fields.Char(
        "Channel name", related="sale_channel_id.name", readonly=True
    )
    edi_desadv = fields.Boolean(
        "Edi Desadv", related="partner_id.edi_desadv", readonly=True
    )

    @api.model
    def _invoice_create_line(self, moves, journal_id, inv_type="out_invoice"):
        res = super(StockPicking, self)._invoice_create_line(
            moves, journal_id, inv_type
        )
        if self.env.context.get("split_invoice_lines", False):
            for invoice in self.env["account.invoice"].browse(res):
                for line in invoice.invoice_line:
                    if line.move_id.linked_move_operation_ids:
                        if len(line.move_id.linked_move_operation_ids) > 1:
                            for operation in line.move_id.mapped(
                                "linked_move_operation_ids.operation_id"
                            ):
                                line.copy(
                                    {
                                        "quantity": operation.product_qty,
                                        "lot_id": operation.lot_id.id,
                                    }
                                )
                            line.unlink()
                        else:
                            line.lot_id = (
                                line.move_id.linked_move_operation_ids.operation_id.lot_id.id
                            )
        return res

    @api.multi
    def print_package_tag_report(self):
        self.ensure_one()
        custom_data = {
            "pick_id": self.id,
        }
        rep_name = "asperience_edi.package_tag_report"
        rep_action = self.env["report"].get_action(self, rep_name)
        rep_action["data"] = custom_data
        return rep_action

    @api.multi
    def print_palet_tag_report(self):
        self.ensure_one()
        custom_data = {
            "pick_id": self.id,
        }
        rep_name = "asperience_edi.palet_tag_report"
        rep_action = self.env["report"].get_action(self, rep_name)
        rep_action["data"] = custom_data
        return rep_action

    @api.multi
    def print_eci_report(self):
        self.ensure_one()
        custom_data = {
            "pick_id": self.id,
        }
        rep_name = "asperience_edi.corte_ingles_report"
        rep_action = self.env["report"].get_action(self, rep_name)
        rep_action["data"] = custom_data
        return rep_action

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        inv_vals = super(StockPicking, self)._get_invoice_vals(
            key, inv_type, journal_id, move
        )
        sale = move.picking_id.sale_id
        if sale and inv_type in ("out_invoice", "out_refund"):
            inv_vals.update(
                {
                    "customer_order": sale.partner_id.id,
                    "customer_payer": sale.customer_payer.id,
                    "customer_department": sale.customer_department,
                }
            )
        return inv_vals


class StockInvoiceOnshipping(models.TransientModel):

    _inherit = "stock.invoice.onshipping"

    split_invoice_lines = fields.Boolean()

    @api.multi
    def create_invoice(self):
        return super(
            StockInvoiceOnshipping,
            self.with_context(split_invoice_lines=self.split_invoice_lines),
        ).create_invoice()
