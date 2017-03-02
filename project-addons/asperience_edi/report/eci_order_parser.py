# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from openerp import models, api


class CorteInglesParser(models.AbstractModel):
    """
    """
    _name = 'report.asperience_edi.eci_order_report'

    def _get_header_table(self, order):

        header_table = {
            'n_order': '????????',
            'n_repo': '',
            'n_deliver': '',
            'supplier_order': '',

            'date': order.date_order,
            'min_date': '??/??/??',
            'top_min_date': '??/??/??',
            'date_settle': '??/??/??',

            'temp': '¿¿OTONNO-INVIERNO??',
            'sale_department': order.customer_department or '',
            'customer_branch': order.customer_branch,
            'deliver_place': '',

            'purchase_department': '???',
            'add_conditions': ''
        }
        return header_table

    def _get_edi_table(self, order):
        edi_table = {
            'emisor': {
                'name': '50-CENTRAL DE COMPRAS GRAN\n\
                        CONSUMO',
                'vat': '(A28017895)',
                'gln': '8422416000504',
                'street': 'CL/HERMOSILLA, 112 MADRID',
                'city': '',
                'state': '',
                'zip': '28009',
            },
            'supplier': {
                'name': 'PROCESOS FARMACEUTICOS\n\
                        INDUSTRIALES',
                'vat': '(B24470171)',
                'gln': '8437008000008',
                'street': 'P.IND DE CAMPONARAYA SECTOR 2 PARCELA 3',
                'city': 'CAMPONARAYA',
                'state': '',
                'zip': '24410',
            },
            'dest_branch': {
                'name': 'ALMACÉN ECI VALDEMORO 1 050\n\
                        CONSUMO',
                'vat': '(A28023895)',
                'gln': '8422416000504',
                'street': 'CTRA. ANDALUCIA K23, MARGEN IZQUI',
                'city': 'VALDEMORO',
                'state': '',
                'zip': '28340',
            },
            'msg_receptor': {
                'name': 'PROCESOS FARMACEUTICOS\n\
                        INDUSTRIALES',
                'vat': '(B24470171)',
                'gln': '8437008000008',
                'street': 'P.IND DE CAMPONARAYA SECTOR 2 PARCELA 3',
                'city': 'CAMPONARAYA',
                'state': '',
                'zip': '24410',
            },
            'delivery_branch': {
                'name': 'ALMACÉN ECI VALDEMORO 1 050\n\
                        CONSUMO',
                'vat': '(A28023895)',
                'gln': '8422416000504',
                'street': 'CTRA. ANDALUCIA K23, MARGEN IZQUI',
                'city': 'VALDEMORO',
                'state': '',
                'zip': '28340',
            },
            'invoice_entity': {
                'name': 'ALMACÉN ECI VALDEMORO 1 050\n\
                        CONSUMO',
                'vat': '(A28023895)',
                'gln': '8422416000504',
                'street': 'CTRA. ANDALUCIA K23, MARGEN IZQUI',
                'city': 'VALDEMORO',
                'state': '',
                'zip': '28340',
            }
        }
        return edi_table

    def _get_lines_table(self, order):
        lines_table = {}
        for l in order.order_line:
            lines_table[l] = {
                'ean13': '1234567891234',
                'ean14': '12345678912343',
                'ref_eci': l.product_id.eci_ref,
                'description': l.product_id.name,
                'property': '???',
                'qty': l.product_uom_qty,
                'uom': l.product_uom.name,
                'pack_units': l.units_per_package,
                'disc': l.discount or '',
                'pvp': l.price_unit,
                'subtotal': l.price_subtotal,
            }
        return lines_table

    @api.multi
    def render_html(self, data=None):
        report_obj = self.env['report']
        order_obj = self.env['sale.order']
        report_name = 'asperience_edi.eci_order_report'
        order = order_obj.browse(data['sale_id'])

        header_table = self._get_header_table(order)
        edi_table = self._get_edi_table(order)
        lines_table = self._get_lines_table(order)

        docargs = {
            'doc_ids': [order.id],
            'doc_model': 'stock.ordering',
            'docs': [order],
            'header_table': header_table,
            'edi_table': edi_table,
            'lines_table': lines_table
        }
        return report_obj.render(report_name, docargs)
