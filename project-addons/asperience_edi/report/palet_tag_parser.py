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
        # import ipdb; ipdb.set_trace()
        pick = pick_obj.browse(data['pick_id'])
        package_dic = palet_dic = {}
        num_palets = palet_number = 0

        for op in pick.pack_operation_ids:
            # ETIQUETAS DE BULTO
            if op.product_id not in package_dic:
                package_dic[op.product_id] = []

            num_packs = op.complete + (1 if op.package else 0)
            for i in range(2 * num_packs):
                dic = {
                    'description': op.product_id.name,
                    'serial_number': op.product_id.ean13,
                    'lot': op.lot_id.name if op.lot_id else '-',
                    'num_units': '12/36',
                    'barcode': '184 33329 03229 9',
                }
                package_dic[op.product_id].append(dic)

            # ETIQUETAS DE PALET
            if not op.palet:
                continue
            if op.palet not in palet_dic:
                palet_number += 1
                num_palets += 1
                palet_dic[op.palet] = {
                    'place': 'ALMACÉN VALDEMORO 1 050',
                    'place_dir': 'CTRA ANDALUCÍA K23, MARGEN IZQ;\
                                  28340_VALDEMORO\n(Madrid)',
                    'num_packs': 0,
                    'palet_number': palet_number,
                    'barcode': '',
                }

            num_packs = op.complete + (1 if op.package else 0)
            palet_dic[op.palet]['num_packs'] += num_packs
            if op.sscc:
                palet_dic[op.palet]['barcode'] += op.sscc

        docargs = {
            'doc_ids': [],
            'doc_model': 'stock.picking',
            'docs': pick,
            'package_dic': package_dic,
            'palet_dic': palet_dic,
            'num_palets': num_palets
        }
        # import ipdb; ipdb.set_trace()
        print package_dic
        return report_obj.render(report_name, docargs)
