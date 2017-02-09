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
from datetime import datetime
import time

class edi_parser(models.Model):

    _name = 'edi.parser'

    def parse_invoic(self, cr, uid, edi, data, context, _logger, structs):
        invoice_obj = self.pool.get('account.invoice')
        context['model_log'] = 'account.invoice'
        context['ids_log'] = context['active_ids']
        for invoice in invoice_obj.browse(cr, uid, context['active_ids']):
            filename = time.strftime('INVOIC_' + invoice.number.replace('/',"") + '_%Y%m%d%H%M', time.localtime(time.time()))
            data[filename] = []
            _logger.info("Factura %s" % (str(invoice.id)))
            CAB = {
                'lineId': "INVOIC_D_93A_UN_EAN007"
            }
            data[filename].append(edi._create_line_csv(CAB,structs))
            INV = {
                'lineId': "INV",
                'col1': invoice.number,
                'col2': invoice.type == "out_invoice" and "380" or "381",
                'col3': "9"
            }
            data[filename].append(edi._create_line_csv(INV,structs))
            DTM = {
                'lineId': 'DTM',
                'col1': invoice.date_invoice.replace("-",""),
            }
            data[filename].append(edi._create_line_csv(DTM,structs))
            if invoice.payment_mode_id and invoice.payment_mode_id.edi_code:
                PAI = {
                    'lineId': 'PAI',
                    'col1': invoice.payment_mode_id.edi_code
                }
                data[filename].append(edi._create_line_csv(PAI,structs))
            if invoice.type == "out_refund" and invoice.origin_invoices_ids:
                RFF = {
                    'lineId': 'RFF',
                    'col1':  'IV',
                    'col2': invoice.type == "out_refund" and invoice.origin_invoices_ids
                }
            elif invoice.type == "out_invoice" and invoice.origin:
                RFF = {
                    'lineId': 'RFF',
                    'col1': invoice.origin.startswith("SO") and 'ON' or 'DQ',
                    'col2': invoice.origin
                }
            else:
                RFF = False
            if RFF:
                data[filename].append(edi._create_line_csv(RFF,structs))
            NADSU = {
                'lineId': 'NADSU',
                'col1': invoice.company_id.partner_id.gln,
                'col2': invoice.company_id.name,
                'col3': " ",
                'col4': invoice.company_id.street or " ",
                'col5': invoice.company_id.city or " ",
                'col6': invoice.company_id.zip or " ",
                'col7': invoice.company_id.vat or " "
            }
            data[filename].append(edi._create_line_csv(NADSU,structs))
            FACT = {
                'lineId': 'NADBY',
                'col1': invoice.partner_id.commercial_partner_id.gln,
                'col2': invoice.partner_id.commercial_partner_id.name,
                'col3': invoice.partner_id.commercial_partner_id.street or " ",
                'col4': invoice.partner_id.commercial_partner_id.city or " ",
                'col5': invoice.partner_id.commercial_partner_id.zip or " ",
                'col6': invoice.partner_id.commercial_partner_id.vat or " "
            }
            data[filename].append(edi._create_line_csv(FACT,structs))
            FACT['lineId'] = "NADIV"
            data[filename].append(edi._create_line_csv(FACT,structs))
            NADDP = {
                'lineId': 'NADDP',
                'col1': invoice.partner_id.gln,
                'col2': invoice.partner_id.name,
                'col3': invoice.partner_id.street or " ",
                'col4': invoice.partner_id.city or " ",
                'col5': invoice.partner_id.zip or " "
            }
            data[filename].append(edi._create_line_csv(NADDP,structs))
            CUX = {
                'lineId': 'CUX',
                'col1': invoice.currency_id.name,
                'col2': '4'
            }
            data[filename].append(edi._create_line_csv(CUX,structs))
            fin_seq = 1
            if invoice.commercial_discount_amount > 0.0:
                fin_seq = 2
                ALC = {
                    'lineId': 'ALC',
                    'col1': 'A',
                    'col2': '1',
                    'col3': 'TD',
                    'col4': invoice.commercial_discount_input,
                    'col5': invoice.commercial_discount_amount,

                }
                data[filename].append(edi._create_line_csv(ALC, structs))
            if invoice.financial_discount_amount > 0.0:

                ALC = {
                    'lineId': 'ALC',
                    'col1': 'A',
                    'col2': str(fin_seq),
                    'col3': 'TD',
                    'col4': invoice.financial_discount_input,
                    'col5': invoice.financial_discount_amount,

                }
                data[filename].append(edi._create_line_csv(ALC, structs))
            for line in invoice.invoice_line:
                if not line.product_id.ean13:
                    raise exceptions.Warning(_('EAN Error'), _('The product %s not has an EAN') % line.product_id.name)
                LIN = {
                    'lineId': 'LIN',
                    'col1': line.product_id.ean13 or '',
                    'col2': "EN"
                }
                data[filename].append(edi._create_line_csv(LIN,structs))
                if line.lot_id:
                    PIALIN = {
                        'lineId': 'PIALIN',
                        'col1': '',
                        'col2': '',
                        'col3': '',
                        'col4': '',
                        'col5': line.lot_id.name,
                        'col6': '',
                        'col7': '',
                        'col8': '',
                    }
                    data[filename].append(edi._create_line_csv(PIALIN, structs))
                IMDLIN = {
                    'lineId': 'IMDLIN',
                    'col1': line.name,
                    'col2': 'M',
                    'col3': 'F'
                }
                data[filename].append(edi._create_line_csv(IMDLIN,structs))
                QTYLIN = {
                    'lineId': 'QTYLIN',
                    'col1': '47',
                    'col2': line.quantity,
                    'col3': line.uos_id.edi_code or 'PCE'
                }
                data[filename].append(edi._create_line_csv(QTYLIN,structs))
                MOALIN = {
                    'lineId': 'MOALIN',
                    'col1': line.price_subtotal,
                }
                data[filename].append(edi._create_line_csv(MOALIN,structs))
                PRILIN = {
                    'lineId': 'PRILIN',
                    'col1': 'AAA',
                    'col2': line.price_unit * (1 - ((line.discount or 0.0) / 100.0)),
                    'col3': line.uos_id.edi_code or 'PCE'
                }
                data[filename].append(edi._create_line_csv(PRILIN,structs))
                if line.discount:
                    PRILIN = {
                        'lineId': 'PRILIN',
                        'col1': 'AAB',
                        'col2': line.price_unit,
                        'col3': line.uos_id.edi_code or 'PCE'
                    }
                    data[filename].append(edi._create_line_csv(PRILIN,structs))
                for tax in line.invoice_line_tax_id:
                    TAXLIN = {
                        'lineId': 'TAXLIN',
                        'col1': 'VAT',
                        'col2': round(tax.amount * 100.0),
                        'col3': line.price_subtotal * tax.amount,
                    }
                    data[filename].append(edi._create_line_csv(TAXLIN,structs))
                if line.discount:
                    ALCLIN = {
                        'lineId': 'ALCLIN',
                        'col1': 'A',
                        'col2': '1',
                        'col3': 'TD',
                        'col4': '',
                        'col5': line.discount,
                        'col6': line.discounted_amount,
                    }
                    data[filename].append(edi._create_line_csv(ALCLIN, structs))
            CNTRES = {
                'lineId': 'CNTRES',
                'col1': '2'
            }
            data[filename].append(edi._create_line_csv(CNTRES,structs))
            MOARES = {
                'lineId': 'MOARES',
                'col1': invoice.amount_untaxed,
                'col2': sum([x.price_unit * x.quantity for x in invoice.invoice_line]),
                'col3': invoice.amount_untaxed,
                'col4': invoice.amount_total,
                'col5': invoice.amount_tax,
            }
            data[filename].append(edi._create_line_csv(MOARES,structs))
            for tax in invoice.tax_line:
                if tax.base != 0.0:
                    TAXRES = {
                        'lineId': 'TAXRES',
                        'col1': 'VAT',
                        'col2': int(round((tax.amount / tax.base) * 100.0)),
                        'col3': tax.amount,
                        'col4': tax.base,
                    }
                else:
                    TAXRES = {
                        'lineId': 'TAXRES',
                        'col1': 'VAT',
                        'col2': 0,
                        'col3': tax.amount,
                        'col4': tax.base,
                    }
                data[filename].append(edi._create_line_csv(TAXRES,structs))
            context['model_log'] = 'account.invoice'
            context['id_log'] = invoice.id
            context['filename'] = filename
            self.pool.get('edi.edi')._log(cr, uid, [edi.id], context)
            return data

    def _checksum(self,sscc):
        """Devuelve el sscc pasado mas un dígito calculado"""
        iSum = 0
        for i in xrange(len(sscc)-1,-1,-2):
            iSum += int(sscc[i])
        iSum *= 3
        for i in xrange(len(sscc)-2,-1,-2):
            iSum += int(sscc[i])

        iCheckSum = (10 - (iSum % 10)) % 10

        return "%s%s" % (sscc, iCheckSum)

    def make_sscc(self, cr, uid, context=None):
        """Método con el que se calcula el sscc a partir del 1+ aecoc + una sequencia de 6 caracteres + 1 digito checksum
        para escribir en el name del paquete"""
        sequence = self.pool.get('ir.sequence').get(cr, uid, 'scc.tracking.sequence') #sequencia definida en sscc_sequence.tracking
        aecoc = self.pool.get('res.users').browse(cr,uid,uid).company_id.aecoc_code
        try:
            return str(self._checksum("1" + aecoc + sequence ))
        except Exception:
            return sequence

    def parse_desadv(self, cr, uid, edi, data, context, _logger, structs):
        pick_obj = self.pool.get('stock.picking')
        context['model_log'] = 'stock.picking'
        context['ids_log'] = context['active_ids']
        for pick in pick_obj.browse(cr, uid, context['active_ids'], context):
            if not pick.partner_id.gln :
                raise exceptions.Warning(_('GLN Error'), _('The partner %s does not have GLN configured') % pick.partner_id.name)
            if not pick.partner_id.commercial_partner_id.gln:
                raise exceptions.Warning(_('GLN Error'), _('The partner %s does not have GLN configured') % pick.partner_id.commercial_partner_id.name)
            if not pick.company_id.partner_id.gln:
                raise exceptions.Warning(_('GLN Error'), _('The partner %s does not have GLN configured') % pick.company_id.partner_id.name)
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

            MOA = {
                'lineId': 'MOA',
                'col1': str(pick.amount_gross),
                'col2': str(pick.amount_untaxed),
            }
            data[filename].append(edi._create_line_csv(MOA,structs))

            ALI = {
                'lineId': 'ALI',
                'col1': 'X7',
            }
            data[filename].append(edi._create_line_csv(ALI,structs))

            RFF = {
                'lineId': 'RFF',
                'col1': 'ON',
                'col2': pick.sale_id.name
            }
            data[filename].append(edi._create_line_csv(RFF,structs))

            NADMS = {
                'lineId': 'NADMS',
                'col1': pick.company_id.partner_id.gln
            }
            data[filename].append(edi._create_line_csv(NADMS,structs))
            NADMR = {
                'lineId': 'NADMR',
                'col1': pick.partner_id.commercial_partner_id.gln
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

            # Se recorren las operaciones ya que contienen los datos de empaquetado.
            curr_pal = False
            curr_sscc = False
            for line in sorted(pick.pack_operation_ids, key=lambda x: x.palet):
                for move_link in line.linked_move_operation_ids:
                    if not line.product_id.ean13:
                        raise exceptions.Warning(_('EAN Error'), _('The product %s not has an EAN') % line.product_id.name)
                    if line.palet != curr_pal:
                        curr_pal = line.palet
                        CPS = {
                            'lineId': 'CPS',
                            'col1': line.palet + 1,
                            'col2': 1
                        }
                        data[filename].append(edi._create_line_csv(CPS, structs))

                        PAC = {
                            'lineId': 'PAC',
                            'col1': '201'
                        }
                        data[filename].append(edi._create_line_csv(PAC, structs))
                        if not line.sscc:
                            curr_sscc = self.make_sscc(cr, uid, context)
                            line.with_context(no_recompute=True).write({'sscc': curr_sscc})
                        else:
                            curr_sscc = line.sscc

                        PCI = {
                            'lineId': 'PCI',
                            'col1': '33E',
                            'col2': 'BJ',
                            'col3': curr_sscc
                        }
                        data[filename].append(edi._create_line_csv(PCI, structs))
                    # si la linea no tiene sscc se le escribe el actual
                    elif not line.sscc:
                        line.with_context(no_recompute=True).write({'sscc': curr_sscc})
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
                        'col2': move_link.qty,
                        'col3': line.product_uom_id.edi_code or 'PCE'
                    }
                    data[filename].append(edi._create_line_csv(QTYLIN,structs))
                    MOALIN = {
                        'lineId': 'MOALIN',
                        'col1': str(move_link.move_id.price_subtotal_gross),
                        'col2': str(move_link.move_id.price_subtotal),
                        'col3': str(move_link.move_id.price_total),
                    }
                    data[filename].append(edi._create_line_csv(MOALIN,structs))

                    LOCLIN = {
                        'lineId': 'LOCLIN',
                        'col1': pick.partner_id.gln
                    }
                    data[filename].append(edi._create_line_csv(LOCLIN, structs))
                    PCILIN = {
                        'lineId': 'PCILIN',
                        'col1': '36E',
                        'col2': line.lot_id.life_date and line.lot_id.life_date.split(" ")[0].replace("-","") or '',
                        'col3': '',
                        'col4': '',
                        'col5': '',
                        'col6': '',
                        'col7': '',
                        'col8': line.lot_id.name,
                    }
                    data[filename].append(edi._create_line_csv(PCILIN, structs))

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

    def parse_recadv(self, cr, uid, edi, data, filename):
        pick_obj = self.pool.get('stock.picking')
        move_obj = self.pool.get('stock.move')
        partner_obj = self.pool.get('res.partner')
        product_obj = self.pool.get('product.product')
        uom_obj = self.pool.get('product.uom')
        vals = {}
        old_pick_id = False
        new_pick_id = False
        possible_move_ids = []
        visited_moves = []
        return_moves = []
        for line in data[filename]:
            if line and line[0] == 'BGM':
                vals = {}
                vals['origin'] = line[1]['numdoc']
            elif line and line[0] == 'DTM':
                vals['date'] = line[1]['date'] and datetime.strftime(datetime.strptime(line[1]['date'], "%Y%m%d"), '%Y-%m-%d %H:%M:%S') or time.strftime('%Y-%m-%d %H:%M:%S')
                vals['min_date'] = line[1]['min_date'] and datetime.strftime(datetime.strptime(line[1]['min_date'], "%Y%m%d"), '%Y-%m-%d %H:%M:%S') or time.strftime('%Y-%m-%d %H:%M:%S')
            elif line and line[0] == 'RFF':
                old_pick_id = pick_obj.search(cr, uid, [('name', '=', line[1]['ref'])])
                if not old_pick_id:
                    raise Exception("No se ha encontrado el albarán referenciado %s" % line[1]['ref'])
                else:
                    old_pick_id = old_pick_id[0]
            elif line and line[0] == 'NADMS':
                partner_id = partner_obj.search(cr, uid, [('gln', '=', line[1]['emisor'])])
                if not partner_id:
                    raise Exception("El emisor con gln %s no se ha encontrado" % (line[1]['emisor']))
                else:
                    vals['partner_id'] = partner_id[0]
            elif line and line[0] == 'NADDP':
                partner_id = partner_obj.search(cr, uid, [('gln', '=', line[1]['destino'])])
                if not partner_id:
                    raise Exception("El destinatario con gln %s no se ha encontrado" % (line[1]['destino']))
                else:
                    vals['partner_id'] = partner_id[0]
            elif line and 'LIN' in line[0]:
                if line[0] == 'LIN':
                    possible_move_ids = move_obj.search(cr, uid, [('picking_id', '=', old_pick_id),('product_id.ean13', '=', line[1]['ean13'][:13]),('id', 'not in', visited_moves)])
                    if not possible_move_ids:
                        raise Exception("No se ha encontrado el producto con ean13 %s en el albaran con id %s" % (line[1]['ean13'][:13], old_pick_id))
                elif line[0] == 'QTYLIN' and possible_move_ids:
                    move = False
                    for pos_move in move_obj.browse(cr, uid, possible_move_ids):
                        if pos_move.product_uom_qty == float(line[1]['enviadas']):
                            visited_moves.append(pos_move.id)
                            move = pos_move
                            break
                    if move.product_uom_qty != float(line[1]['aceptadas']):
                        return_moves.append((move, move.product_uom_qty - float(line[1]['aceptadas'])))
        if return_moves:
            return_wzd = self.pool.get('stock.return.picking').create(cr, uid, {'invoice_state': '2binvoiced'})
            for move_data in return_moves:
                    self.pool.get('stock.return.picking.line').create(cr, uid, {'product_id': move_data[0].product_id.id,
                                                                                'quantity': move_data[1],
                                                                                'wizard_id': return_wzd,
                                                                                'move_id': move_data[0].id})
            return_view = self.pool.get('stock.return.picking').create_returns(cr, uid, [return_wzd], {'active_ids': [old_pick_id], 'active_id': old_pick_id})
            new_pick_id = eval(return_view['domain'])[0][2]
            pick_obj.write(cr, uid, new_pick_id, vals)
