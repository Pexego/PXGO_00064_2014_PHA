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
    def get_tag_info(self, op, pack_table_class, lot_name=False, qty=False):
        serie = op.product_id.ean13 and op.product_id.ean13[:-1] or ''
        digits = map(int, '1' + serie)
        check_digit = self.calculate_check_digit(digits)
        barcode = serie and \
            '1 ' + serie[0:2] + ' ' + serie[2:7] + ' ' + serie[7:]\
            + ' ' + str(check_digit) or ''
        cant_ue = str(op.product_id.box_elements)

        name_lot = lot_name if lot_name else \
            (op.lot_id.name if op.lot_id else '-')
        quantity = qty if qty else (op.product_qty)
        dic = {
            'description': op.product_id and
            op.product_id.name.upper() or '',
            'serial_number': serie,
            'lot': name_lot,
            'num_units': str(cant_ue) + '/' + str(quantity),
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
        for op in pick.pack_operation_ids:
            # ETIQUETAS DE BULTO
            if op.product_id not in package_dic:
                package_dic[op.product_id] = []
            # 2 Etiquetas por bulto completo
            num_packs = op.complete
            for i in range(2 * num_packs):
                dic = self.get_tag_info(op, pack_table_class)
                pack_table_class == 2 if pack_table_class == 1 else 1
                package_dic[op.product_id].append(dic)

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

                total_packs = palet_packs_dic.get(op.palet, 0)
                palet_dic[op.palet] = {
                    'place': pick.partner_id.street2 and
                    pick.partner_id.street2 or '',
                    'place_dir': pick.partner_id.street and
                    pick.partner_id.street.upper() or '',
                    'num_packs': total_packs,
                    'palet_number': palet_number,
                    'barcode': '',
                }
            if op.sscc:
                palet_dic[op.palet]['barcode'] = '(00)' + op.sscc

        # Sumar cantidades y lotes en los paquetes parciales:
        for package in partial_packs:
            lot_ids = []
            units = 0
            lot_name = ''
            for op in partial_packs[package]:
                units += op.product_qty
                if op.lot_id.id not in lot_ids:
                    lot_ids.append(op.lot_id.id)
                    lot_name += op.lot_id.name if not lot_name \
                        else ' / ' + op.lot_id.name

            for i in range(2):
                dic = self.get_tag_info(op, pack_table_class, lot_name, units)
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
