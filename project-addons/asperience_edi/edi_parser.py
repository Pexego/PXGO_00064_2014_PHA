# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2016 Comunitea All Rights Reserved
#    $Jesús Ventosinos Mayor <jesus@comunitea.com>$
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
from openerp import models, fields, api, exceptions, _
import time

class edi_parser(models.Model):

    _name = 'edi.parser'

    def parse_desadv(self, cr, uid, edi, data, context, _logger, structs):
        pick_obj = self.pool.get('stock.picking')
        context['model_log'] = 'stock.picking'
        context['ids_log'] = context['active_ids']
        for pick in pick_obj.browse(cr, uid, context['active_ids'], context):
            filename = time.strftime('ALB_' + pick.name.replace('/',"").replace('\\',"").replace(' ',"") + '_%Y%m%d%H%M', time.localtime(time.time()))
            data[filename] = []
            _logger.info("Albaran %s" % (str(pick.id)))
            CAB = {
                'lineId': "DESADV_D_96A_UN_EAN005"
            }
            data[filename].append(edi._create_line_csv(CAB,structs))
            BGM = {
                'lineId': "BGM",
                'col1': pick.name,
                'col2': "351",
                'col3': "9"
            }
            data[filename].append(edi._create_line_csv(BGM,structs))
            DTM = {
                'lineId': 'DTM',
                'col1': time.strftime("%Y%m%d"),
                'col2': pick.min_date.split(" ")[0].replace("-","")
            }
            data[filename].append(edi._create_line_csv(DTM,structs))
            '''MOA = {
                'lineId': 'MOA',
                'col1': pick.amount_total,
                'col2': pick.amount_untaxed
            }
            data[filename].append(edi._create_line_csv(MOA,structs))'''
            NADMS = {
                'lineId': 'NADMS',
                'col1': pick.company_id.partner_id.gln
            }
            data[filename].append(edi._create_line_csv(NADMS,structs))
            NADMR = {
                'lineId': 'NADMR',
                'col1': pick.partner_id.gln
            }
            data[filename].append(edi._create_line_csv(NADMR,structs))
            NADDP = {
                'lineId': 'NADDP',
                'col1': pick.partner_id.gln,
            }
            data[filename].append(edi._create_line_csv(NADDP,structs))
            CPS = {
                'lineId': 'CPS',
                'col1': 1,
            }
            data[filename].append(edi._create_line_csv(CPS,structs))
            for line in pick.move_lines:
                LIN = {
                    'lineId': 'LIN',
                    'col1': line.product_id.ean13,
                    'col2': "EN"
                }
                data[filename].append(edi._create_line_csv(LIN,structs))
                IMDLIN = {
                    'lineId': 'IMDLIN',
                    'col1': 'F',
                    'col2': line.product_id.name
                }
                data[filename].append(edi._create_line_csv(IMDLIN,structs))
                QTYLIN = {
                    'lineId': 'QTYLIN',
                    'col1': '12',
                    'col2': line.product_uom_qty,
                    'col3': line.product_uom.edi_code or 'PCE'
                }
                data[filename].append(edi._create_line_csv(QTYLIN,structs))
            CNTRES = {
                'lineId': 'CNTRES',
                'col1': sum([x.product_uom_qty for x in pick.move_lines]),
                'col2': pick.weight,
                'col3': len(pick.move_lines),
                'col4': pick.number_of_packages or "",
                'col5': pick.weight_net
            }
            data[filename].append(edi._create_line_csv(CNTRES,structs))
            context['model_log'] = 'stock.picking'
            context['id_log'] = pick.id
            context['filename'] = filename
            self.pool.get('edi.edi')._log(cr, uid, [edi.id], context)
            return data
