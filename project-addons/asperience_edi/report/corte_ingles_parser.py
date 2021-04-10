# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api
from openerp.exceptions import except_orm
from dateutil import parser


class CorteInglesParser(models.AbstractModel):
    """"""

    _name = "report.asperience_edi.corte_ingles_report"

    def _get_header_table(self, pick):

        date = parser.parse(pick.date)
        date_str = date.strftime("%d/%m/%Y")

        min_date = parser.parse(pick.min_date)
        min_date_str = min_date.strftime("%d/%m/%Y %H:%M")

        s = pick.sale_id
        pick_partner = pick.partner_id
        if pick_partner.type in ["delivery"] and pick_partner.parent_id:
            pick_partner = pick_partner.parent_id
        header_table = {
            "enterprise": pick_partner.edi_partner,
            "dest_branch": s and s.customer_branch or "",
            "department": s and s.customer_department or "",
            "eci_supplier": pick_partner.edi_supplier_ref,
            "date": date_str,
            "min_date": min_date_str,
            "order_number": s.client_order_ref,
            "pick_number": pick.name,
        }
        return header_table

    def _get_edi_table(self, pick):
        edi_entities = {
            "agency": pick.company_id.partner_id,
            "supplier": pick.company_id.partner_id,
            "dest_branch": pick.sale_id and pick.sale_id.customer_transmitter or False,
            "msg_receptor": pick.sale_id and pick.sale_id.partner_id or False,
            "delivery_branch": pick.partner_id,
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

    def _get_palet_tables(self, pick):
        palet_tables = {}
        total_tables = {}

        p_table = {}
        first = True
        op_by_product = {}
        visited_products_by_palet = {}

        # Group operations by product
        for op in pick.pack_operation_ids:
            if op.product_id.id not in op_by_product:
                op_by_product[op.product_id.id] = {}
            if op.palet and op.palet not in op_by_product[op.product_id.id].keys():
                op_by_product[op.product_id.id][op.palet] = 0.0
            op_by_product[op.product_id.id][op.palet] += op.product_qty

        for op in pick.pack_operation_ids:
            if op.palet and op.palet not in visited_products_by_palet.keys():
                visited_products_by_palet[op.palet] = []
            if not op.palet or op.product_id.id in visited_products_by_palet.get(op.palet):
                continue

            if op.palet not in palet_tables:
                palet_tables[op.palet] = []
            if op.palet not in total_tables:
                total_packs = len(
                    op.sscc_ids.filtered(lambda x: x.type == "1").child_ids
                )
                total_tables[op.palet] = {
                    "total_qty": 0.0,
                    "total_lines": 0.0,
                    "total_packs": total_packs,
                    "first": first,
                }
                first = False
            cant_ue = str(op.product_id.box_elements)
            ref_eci = ""
            pick_partner = pick.partner_id
            for cus in op.product_id.customer_ids:
                if pick_partner.type in ["delivery"] and pick_partner.parent_id:
                    pick_partner = pick_partner.parent_id
                if cus.name.id == pick_partner.id:
                    ref_eci = cus.product_code
            gtin14 = ""
            gtin_partner = pick.partner_id
            if gtin_partner.type in ["delivery"] and gtin_partner.parent_id:
                gtin_partner = gtin_partner.parent_id
            for gtin_obj in op.product_id.gtin14_ids:
                for part in gtin_obj.partner_ids:
                    if part.id == gtin_partner.id:
                        gtin14 = gtin_obj.gtin14
                        cant_ue = str(gtin_obj.units)
            p_table = {
                "ean13": op.product_id.ean13,
                "serie": op.product_id.ean13 and op.product_id.ean13[:-1] or "",
                "ref_eci": ref_eci,
                "description": op.product_id.name.upper(),
                "cant_ue": cant_ue,
                "cant_fact": op_by_product[op.product_id.id][op.palet],
                "cant_no_fact": "",
                "ean14": gtin14,
            }
            palet_tables[op.palet].append(p_table)
            visited_products_by_palet[op.palet].append(op.product_id.id)
            total_tables[op.palet]["total_qty"] += p_table["cant_fact"]
            total_tables[op.palet]["total_lines"] += 1

            palet_sscc = op.sscc_ids.filtered(lambda x: x.type == "1")
            if palet_sscc:
                total_tables[op.palet]["sscc"] = palet_sscc.name

        return palet_tables, total_tables

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env["report"]
        pick_obj = self.env["stock.picking"]
        report_name = "asperience_edi.corte_ingles_report"
        pick = pick_obj.browse(data["pick_id"])
        header_table = self._get_header_table(pick)
        edi_table = self._get_edi_table(pick)
        palet_tables, total_tables = self._get_palet_tables(pick)

        if not palet_tables:
            raise except_orm("Error", "Not palets defined in pick operations")

        docargs = {
            "doc_ids": [pick.id],
            "doc_model": "stock.picking",
            "docs": [pick],
            "header_table": header_table,
            "edi_table": edi_table,
            "palet_tables": palet_tables,
            "total_tables": total_tables,
        }
        return report_obj.render(report_name, docargs)
