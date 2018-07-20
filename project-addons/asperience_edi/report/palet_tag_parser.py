# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api
from openerp.exceptions import except_orm
from openerp.tools.translate import _


class PaletTagParser(models.AbstractModel):
    """
    """
    _name = 'report.asperience_edi.palet_tag_report'

    @api.model
    def calculate_check_digit(self, digits):
        res = sum(map(lambda x: x * 3, digits[::2])) + sum(digits[1::2])
        rounded_res = int(round(res, -1))
        if rounded_res == 0:
            rounded_res = 10
        return abs(res - rounded_res)

    @api.model
    def get_tag_info(self, op, pack_table_class, prod_lot_qty,
                     qty_by_lot={}):
        serie = op.product_id.ean13 and op.product_id.ean13[:-1] or ''

        gtin14 = ''
        gtin_partner = op.picking_id.partner_id
        if gtin_partner.type in ['delivery'] and gtin_partner.parent_id:
            gtin_partner = gtin_partner.parent_id
        for gtin_obj in op.product_id.gtin14_ids:
            for part in gtin_obj.partner_ids:
                if part.id == gtin_partner.id:
                    gtin14 = gtin_obj.gtin14
        barcode = ''
        if len(gtin14) == 14:
            parts = \
                [gtin14[0], gtin14[1:3], gtin14[3:8], gtin14[8:13], gtin14[13]]
            barcode = ' '.join(parts)

        # SI hay varios lotes en el paquete, imprimimos los nombres de los
        # lotes y la cantidad de cada uno.
        name_lot = ''
        qty_units_str = ''
        for lot in qty_by_lot:
            lot_qty = qty_by_lot[lot]
            total_lot_qty = prod_lot_qty[op.product_id.id][lot.id]
            name_lot += lot.name if not name_lot \
                else ' / ' + lot.name
            qty_str = str(int(lot_qty)) + '/' + str(int(total_lot_qty))
            qty_units_str += qty_str if not qty_units_str \
                else ' , ' + qty_str

        if not name_lot:
            name_lot = op.lot_id.name if op.lot_id else '-'

        if not qty_units_str:
            cant_ue = op.product_id.box_elements
            total_lot_qty = prod_lot_qty[op.product_id.id][op.lot_id.id]
            qty_units_str = str(int(cant_ue)) + '/' + str(int(total_lot_qty))

        dic = {
            'description': op.product_id and
            op.product_id.name.upper() or '',
            'serial_number': serie,
            'lot': name_lot,
            'num_units': qty_units_str,
            'barcode': barcode,
            'table-class': 'table-%s' % str(pack_table_class)
        }
        return dic

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        pick_obj = self.env['stock.picking']
        report_name = 'asperience_edi.palet_tag_report'
        if not data:
            raise except_orm(_('Error'),
                             _('You must print it from a wizard'))
        pick = pick_obj.browse(data['pick_id'])
        package_dic = {}
        palet_dic = {}
        num_palets = palet_number = 0
        pack_table_class = 1
        palet_packs_dic = pick._get_num_packs_in_palets()
        partial_packs = {}

        prod_lot_qty = {}
        # Agrupar cantidades por lote y producto
        for op in pick.pack_operation_ids:
            if op.product_id.id not in prod_lot_qty:
                prod_lot_qty[op.product_id.id] = {}
            if op.lot_id.id not in prod_lot_qty[op.product_id.id]:
                prod_lot_qty[op.product_id.id][op.lot_id.id] = 0
            prod_lot_qty[op.product_id.id][op.lot_id.id] += op.product_qty

        for op in pick.pack_operation_ids:
            # ETIQUETAS DE BULTO
            if op.product_id not in package_dic:
                package_dic[op.product_id] = []
            # 2 Etiquetas por bulto completo
            num_packs = op.complete
            for i in range(2 * num_packs):
                # Info para paquetes completos, un solo lote
                dic = self.get_tag_info(op, pack_table_class, prod_lot_qty)
                pack_table_class == 2 if pack_table_class == 1 else 1
                package_dic[op.product_id].append(dic)

            # Agrupar los paquetes parciales
            if op.package:
                if op.package not in partial_packs:
                    partial_packs[op.package] = []
                partial_packs[op.package].append(op)

            # ETIQUETAS DE PALET
            if not op.palet:
                continue
            if op.palet not in palet_dic:
                palet_number += 1
                num_palets += 1
                place_dir = [(pick.partner_id.street and
                              pick.partner_id.street.upper() or '')]
                place_dir.append(pick.partner_id.zip)
                place_dir.append(pick.partner_id.city)
                if pick.partner_id.state_id:
                    place_dir.append('(' + pick.partner_id.state_id.name + ')')

                total_packs = palet_packs_dic.get(op.palet, 0)
                palet_dic[op.palet] = {
                    'place': pick.partner_id.name.upper(),
                    'place_dir': ', '.join(place_dir),
                    'num_packs': total_packs,
                    'palet_number': palet_number,
                    'barcode': op.sscc_ids.filtered(lambda x: x.type=='1').name,
                }

        # Proceso paquetes parciales
        for package in partial_packs:
            print package
            qty_by_lot = {}
            # Obtener lotes y cantidades por lote en los paquetes parciales
            # solo de los paquetes parciales, descontando la parte que va en
            # los completos
            print partial_packs[package]
            for op in partial_packs[package]:
                if op.lot_id not in qty_by_lot:
                    qty_by_lot[op.lot_id] = 0
                complete_qty = (op.complete * op.product_id.box_elements)
                qty_by_lot[op.lot_id] += (op.product_qty - complete_qty)
            for i in range(2):
                dic = self.get_tag_info(op, pack_table_class, prod_lot_qty,
                                        qty_by_lot)
                pack_table_class == 2 if pack_table_class == 1 else 1
                package_dic[op.product_id].append(dic)
        docargs = {
            'doc_ids': [],
            'doc_model': 'stock.picking',
            'docs': pick,
            'package_dic': package_dic,
            'palet_dic': palet_dic,
            'num_palets': num_palets
        }
        return report_obj.render(report_name, docargs)
