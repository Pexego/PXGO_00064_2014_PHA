# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api
from dateutil import parser


class CorteInglesParser(models.AbstractModel):
    """"""

    _name = "report.asperience_edi.eci_order_report"

    def _get_header_table(self, order):
        date = parser.parse(order.date_order)
        date_str = date.strftime("%d/%m/%Y")
        top_date_str = ""
        if order.top_date:
            top_date = parser.parse(order.top_date)
            top_date_str = top_date.strftime("%d/%m/%Y")

        header_table = {
            "n_order": order.client_order_ref,
            "n_repo": "",
            "n_deliver": "",
            "supplier_order": "",
            "date": date_str,
            "min_date": "",
            "top_min_date": top_date_str,
            "date_settle": "",
            "temp": "",
            "sale_department": order.customer_department or "",
            "customer_branch": order.customer_branch,
            "deliver_place": "",
            "purchase_department": "",
            "add_conditions": "",
        }
        return header_table

    def _get_edi_table(self, order):
        edi_entities = {
            "emisor": order.customer_transmitter,
            "supplier": order.company_id.partner_id,
            "dest_branch": order.partner_id,
            "msg_receptor": order.company_id.partner_id,
            "delivery_branch": order.partner_shipping_id,
            "invoice_entity": order.partner_invoice_id,
        }

        edi_table = {}
        for k in edi_entities:
            p = edi_entities[k]  # EDI partner entity
            name = vat = gln = street = city = state = zip_ = ""
            if p:
                if p.name:
                    name = p.name.upper()
                if p.vat:
                    vat = "(" + p.vat + ")"
                if p.gln:
                    gln = p.gln
                if p.street:
                    street = p.street.upper()
                if p.city:
                    city = p.city.upper()
                if p.state_id:
                    state = "(" + p.state_id.name + ")"
                if p.zip:
                    zip_ = p.zip
            dic = {
                "name": name,
                "vat": vat,
                "gln": gln,
                "street": street,
                "city": city,
                "state": state,
                "zip": zip_,
            }
            edi_table[k] = dic
        return edi_table

    def _get_lines_table(self, order):
        lines_table = {}
        for l in order.order_line:
            lines_table[l] = {
                "ean13": l.product_id.ean13,
                "ref_eci": l.product_id.get_customer_info(
                    order.partner_id.commercial_partner_id.id
                ),
                "description": l.product_id.name,
                "qty": l.product_uom_qty,
                "pack_units": l.units_per_package or "",
                "pvp": l.net_price,
                "brut_price": l.brut_price,
                "subtotal": l.price_subtotal,
                "serie": l.product_id.ean13 and l.product_id.ean13[:-1] or "",
                "ean14": l.product_id.ean14,
                "subline": l.product_id.subline and l.product_id.subline.name or "",
                "container": l.product_id.container_id
                and l.product_id.container_id.name
                or "",
                "uom": l.product_uom.name,
                "disc": l.discount or "",
            }
        return lines_table

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env["report"]
        order_obj = self.env["sale.order"]
        report_name = "asperience_edi.eci_order_report"
        order = order_obj.browse(data["sale_id"])

        header_table = self._get_header_table(order)
        edi_table = self._get_edi_table(order)
        lines_table = self._get_lines_table(order)

        docargs = {
            "doc_ids": [order.id],
            "doc_model": "stock.ordering",
            "docs": [order],
            "header_table": header_table,
            "edi_table": edi_table,
            "lines_table": lines_table,
        }
        return report_obj.render(report_name, docargs)
