# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class PaletTagParser(models.AbstractModel):
    """"""

    _name = "report.asperience_edi.palet_tag_report"

    @api.model
    def calculate_check_digit(self, digits):
        res = sum(map(lambda x: x * 3, digits[::2])) + sum(digits[1::2])
        rounded_res = int(round(res, -1))
        if rounded_res == 0:
            rounded_res = 10
        return abs(res - rounded_res)

    @api.model
    def get_tag_info(self, op, pack_table_class, prod_lot_qty, sscc, qty_by_lot={}):
        serie = op.product_id.ean13 and op.product_id.ean13[:-1] or ""

        # En lugar de sacar en el cód. de barras el SSCC, vamos a sacar el DUN14
        #        barcode = sscc.name
        partner_id = (
            op.picking_id.partner_id.parent_id
            if op.picking_id.partner_id.parent_id
            else op.picking_id.partner_id
        )
        gtin14_ids = op.product_id.gtin14_ids.with_context(p=partner_id).filtered(
            lambda g: g._context["p"] in g.partner_ids
        )
        barcode = (
            gtin14_ids[0].gtin14 if gtin14_ids else op.product_id.gtin14_default.gtin14
        )

        # SI hay varios lotes en el paquete, imprimimos los nombres de los
        # lotes y la cantidad de cada uno.
        name_lot = ""
        qty_units_str = ""
        for lot in qty_by_lot:
            lot_qty = qty_by_lot[lot]
            total_lot_qty = prod_lot_qty[op.product_id.id][lot.id]
            name_lot += lot.name if not name_lot else " / " + lot.name
            qty_str = str(int(lot_qty)) + "/" + str(int(total_lot_qty))
            qty_units_str += qty_str if not qty_units_str else " , " + qty_str

        if not name_lot:
            name_lot = op.lot_id.name if op.lot_id else "-"

        if not qty_units_str:
            cant_ue = op.product_id.box_elements
            total_lot_qty = prod_lot_qty[op.product_id.id][op.lot_id.id]
            qty_units_str = str(int(cant_ue)) + "/" + str(int(total_lot_qty))

        dic = {
            "description": op.product_id and op.product_id.name.upper() or "",
            "serial_number": serie,
            "lot": name_lot,
            "num_units": qty_units_str,
            "barcode": barcode,
            "table-class": "table-%s" % str(pack_table_class),
        }
        return dic

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env["report"]
        pick_obj = self.env["stock.picking"]
        report_name = "asperience_edi.palet_tag_report"
        if not data:
            raise except_orm(_("Error"), _("You must print it from a wizard"))
        pick = pick_obj.browse(data["pick_id"])
        package_dic = {}
        palet_dic = {}
        num_palets = palet_number = 0
        pack_table_class = 1
        partial_packs = {}

        prod_lot_qty = {}
        # Agrupar cantidades por lote y producto
        for op in pick.pack_operation_ids:
            if op.product_id.id not in prod_lot_qty:
                prod_lot_qty[op.product_id.id] = {}
            if op.lot_id.id not in prod_lot_qty[op.product_id.id]:
                prod_lot_qty[op.product_id.id][op.lot_id.id] = 0
            prod_lot_qty[op.product_id.id][op.lot_id.id] += op.product_qty

        for sscc in [
            x for x in pick.mapped("pack_operation_ids.sscc_ids") if x.type == "1"
        ]:
            palet_number += 1
            num_palets += 1
            place_dir = [
                (pick.partner_id.street and pick.partner_id.street.upper() or "")
            ]
            place_dir.append(pick.partner_id.zip)
            place_dir.append(pick.partner_id.city)
            if pick.partner_id.state_id:
                place_dir.append("(" + pick.partner_id.state_id.name + ")")
            op == sscc.operation_ids
            total_packs = len(sscc.child_ids)
            palet_dic[op.palet] = {
                "place": pick.partner_id.name.upper(),
                "place_dir": ", ".join(place_dir),
                "num_packs": total_packs,
                "palet_number": palet_number,
                "barcode": sscc.name,
            }
            for sscc_child in sscc.child_ids.filtered(lambda r: r.type == "2"):
                op = sscc_child.operation_ids
                if op.product_id not in package_dic.keys():
                    package_dic[op.product_id] = []
                # Info para paquetes completos, un solo lote
                dic = self.get_tag_info(op, pack_table_class, prod_lot_qty, sscc_child)
                pack_table_class == 2 if pack_table_class == 1 else 1
                package_dic[op.product_id].append(dic)
                package_dic[op.product_id].append(dic)

            # Proceso paquetes parciales
            for sscc_child in sscc.child_ids.filtered(lambda r: r.type == "3"):
                # En estas etiquetas, los albaranes parciales serán siempre
                # del mismo producto.
                qty_by_lot = {}
                # Obtener lotes y cantidades por lote en los paquetes parciales
                # solo de los paquetes parciales, descontando la parte que va en
                # los completos
                for op in sscc_child.operation_ids:
                    if op.lot_id not in qty_by_lot:
                        qty_by_lot[op.lot_id] = 0
                    complete_qty = op.complete * op.product_id.box_elements
                    qty_by_lot[op.lot_id] += op.product_qty - complete_qty
                for i in range(2):
                    dic = self.get_tag_info(
                        op, pack_table_class, prod_lot_qty, sscc_child, qty_by_lot
                    )
                    pack_table_class == 2 if pack_table_class == 1 else 1
                    if op.product_id not in package_dic.keys():
                        package_dic[op.product_id] = []
                    package_dic[op.product_id].append(dic)
        docargs = {
            "doc_ids": [],
            "doc_model": "stock.picking",
            "docs": pick,
            "package_dic": package_dic,
            "palet_dic": palet_dic,
            "num_palets": num_palets,
        }
        return report_obj.render(report_name, docargs)
