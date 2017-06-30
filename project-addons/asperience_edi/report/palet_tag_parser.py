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
        for op in pick.pack_operation_ids:
            # ETIQUETAS DE BULTO
            if op.product_id not in package_dic:
                package_dic[op.product_id] = []
            num_packs = op.complete + (1 if op.package else 0)
            for i in range(2 * num_packs):
                serie = op.product_id.ean13 and op.product_id.ean13[:-1] or ''
                barcode = serie and \
                    '1 ' + serie[0:2] + ' ' + serie[2:7] + ' ' + serie[7:]\
                    + ' 9' or ''

                cant_ue = ''
                if op.linked_move_operation_ids:
                    if op.linked_move_operation_ids[0].move_id.procurement_id:
                        move = op.linked_move_operation_ids[0].move_id
                        if move.procurement_id:
                            proc = move.procurement_id
                            if proc.sale_line_id:
                                cant_ue = proc.sale_line_id.units_per_package
                    dic = {
                        'description': op.product_id and
                        op.product_id.name.upper() or '',
                        'serial_number': serie,
                        'lot': op.lot_id.name if op.lot_id else '-',
                        'num_units': str(cant_ue) + '/' + str(op.product_qty),
                        'barcode': barcode,
                        'table-class': 'table-%s' % str(pack_table_class)
                    }
                    if pack_table_class == 1:
                        pack_table_class = 2
                    else:
                        pack_table_class = 1
                    package_dic[op.product_id].append(dic)

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

        docargs = {
            'doc_ids': [],
            'doc_model': 'stock.picking',
            'docs': pick,
            'package_dic': package_dic,
            'palet_dic': palet_dic,
            'num_palets': num_palets
        }
        return report_obj.render(report_name, docargs)
