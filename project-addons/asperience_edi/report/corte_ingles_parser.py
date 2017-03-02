# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api
from openerp.exceptions import except_orm


class CorteInglesParser(models.AbstractModel):
    """
    """
    _name = 'report.asperience_edi.corte_ingles_report'

    def _get_header_table(self, pick):
        s = pick.sale_id
        header_table = {
            'enterprise': '??',
            'dest_branch': s and s.customer_branch or '',
            'department': s and s.customer_department or '',
            'eci_supplier': s and False or '???',
            'date': pick.date,
            'min_date': pick.min_date,
            'order_number': s.name + '????',
            'pick_number': pick.name,
        }
        return header_table

    def _get_edi_table(self, pick):
        edi_table = {
            'agency': {
                'name': pick.company_id.partner_id.name.upper(),
                'vat': pick.company_id.partner_id.vat and
                '(' + pick.company_id.partner_id.vat.replace('ES', '') + ')' or
                '',
                'gln': pick.company_id.partner_id.gln,
                'street': pick.company_id.partner_id.street.upper(),
                'city': pick.company_id.partner_id.city.upper(),
                'state': pick.company_id.partner_id.state_id and
                '(' + pick.company_id.partner_id.state_id.name.upper() + ')'or
                '',
                'zip': pick.company_id.partner_id.zip
            },
            'supplier': {
                'name': pick.company_id.partner_id.name.upper(),
                'vat': pick.company_id.partner_id.vat and
                '(' + pick.company_id.partner_id.vat.replace('ES', '') + ')' or
                '',
                'gln': pick.company_id.partner_id.gln,
                'street': pick.company_id.partner_id.street.upper(),
                'city': pick.company_id.partner_id.city.upper(),
                'state': pick.company_id.partner_id.state_id and
                '(' + pick.company_id.partner_id.state_id.name.upper() + ')' or
                '',
                'zip': pick.company_id.partner_id.zip
            },
            'dest_branch': {
                'name': pick.sale_id and pick.sale_id.partner_id and
                pick.sale_id.partner_id.name.upper() or '',
                'vat': pick.sale_id and pick.sale_id.partner_id and
                '(' + pick.sale_id.partner_id.vat.replace('ES', '') + ')'or '',
                'gln': pick.sale_id and pick.sale_id.partner_id and
                pick.sale_id.partner_id.gln or '',
                'street': pick.sale_id and pick.sale_id.partner_id and
                pick.sale_id.partner_id.street.upper() or '',
                'city': pick.sale_id and pick.sale_id.partner_id and
                pick.sale_id.partner_id.city.upper() or '',
                'state': pick.sale_id and pick.sale_id.partner_id and
                pick.sale_id.partner_id.state_id and
                '(' + pick.sale_id.partner_id.state_id.name.upper() + ')' or
                '',
                'zip': pick.sale_id and pick.sale_id.partner_id and
                pick.sale_id.partner_id.zip or ''
            },
            'msg_receptor': {
                'name': pick.sale_id and pick.sale_id.customer_transmitter and
                pick.sale_id.customer_transmitter.name.upper() or '',
                'vat': pick.sale_id and pick.sale_id.customer_transmitter and
                '(' + pick.sale_id.customer_transmitter.vat.replace('ES', '') +
                ')' or '',
                'gln': pick.sale_id and pick.sale_id.customer_transmitter and
                pick.sale_id.customer_transmitter.gln or '',
                'street': pick.sale_id and
                pick.sale_id.customer_transmitter and
                pick.sale_id.customer_transmitter.street.upper() or '',
                'city': pick.sale_id and pick.sale_id.customer_transmitter and
                pick.sale_id.customer_transmitter.city.upper() or '',
                'state': pick.sale_id and pick.sale_id.customer_transmitter and
                pick.sale_id.customer_transmitter.state_id and
                '(' + pick.sale_id.customer_transmitter.state_id.name.upper() +
                ')' or '',
                'zip': pick.sale_id and pick.sale_id.customer_transmitter and
                pick.sale_id.customer_transmitter.zip or ''
            },
            'delivery_branch': {
                'name': pick.partner_id and
                pick.partner_id.name.upper() or '',
                'vat': pick.partner_id and
                '(' + pick.partner_id.vat.replace('ES', '') + ')' or '',
                'gln': pick.partner_id and
                pick.partner_id.gln or '',
                'street': pick.partner_id and
                pick.partner_id.street.upper() or '',
                'city': pick.partner_id and
                pick.partner_id.city.upper() or '',
                'state': pick.partner_id and
                pick.partner_id.state_id and
                '(' + pick.partner_id.state_id.name.upper() + ')' or '',
                'zip': pick.partner_id and
                pick.partner_id.zip or ''
            }
        }
        return edi_table

    def _get_palet_tables(self, pick):
        palet_tables = {}
        total_tables = {}

        p_table = {}
        for op in pick.pack_operation_ids:
            if not op.palet:
                continue

            if op.palet not in palet_tables:
                palet_tables[op.palet] = []
            if op.palet not in total_tables:
                total_tables[op.palet] = {'total_qty': 0.0,
                                          'total_lines': 0.0,
                                          'total_packs': 0.0}
            p_table = {
                'ean13': op.product_id.ean13,
                'ref_eci': op.product_id.eci_ref,
                'description': op.product_id.name.upper(),
                'cant_ue': '???',
                'cant_fact': '???',
                'cant_no_fact': '',
                'ean14': op.product_id.ean13,
            }
            palet_tables[op.palet].append(p_table)

            total_qty = 1
            total_lines = 1
            total_packs = 1

            total_tables[op.palet]['total_qty'] += total_qty
            total_tables[op.palet]['total_lines'] += total_lines
            total_tables[op.palet]['total_packs'] += total_packs
            total_tables[op.palet]['sscc'] = ''
            if op.sscc:
                total_tables[op.palet]['sscc'] = op.sscc

        return palet_tables, total_tables

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        pick_obj = self.env['stock.picking']
        report_name = 'asperience_edi.corte_ingles_report'
        pick = pick_obj.browse(data['pick_id'])
        header_table = self._get_header_table(pick)
        edi_table = self._get_edi_table(pick)
        palet_tables, total_tables = self._get_palet_tables(pick)

        if not palet_tables:
            raise except_orm('Error', 'Not palets defined in pick operations')

        docargs = {
            'doc_ids': [pick.id],
            'doc_model': 'stock.picking',
            'docs': [pick],
            'header_table': header_table,
            'edi_table': edi_table,
            'palet_tables': palet_tables,
            'total_tables': total_tables,
        }
        return report_obj.render(report_name, docargs)
