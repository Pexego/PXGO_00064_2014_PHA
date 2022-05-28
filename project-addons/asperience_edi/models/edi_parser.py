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
from openerp import netsvc
import time


class edi_parser(models.Model):

    _name = "edi.parser"

    def make_partner_changes(self, partner, data, document):
        for edi_change in partner.custom_edi.filtered(lambda r: r.document == document):
            for line in data:
                if line[0] == edi_change.section:
                    for col_index in range(len(line)):
                        if line[col_index] == edi_change.search_value:
                            if edi_change.action == "remove":
                                line[col_index] = ""
                            else:
                                line[col_index] = edi_change.set_value
        return data

    def parse_invoic(self, cr, uid, edi, data, context, _logger, structs):
        invoice_obj = self.pool.get("account.invoice")
        context["model_log"] = "account.invoice"
        context["ids_log"] = context["active_ids"]
        for invoice in invoice_obj.browse(cr, uid, context["active_ids"]):
            filename = time.strftime(
                "INVOIC_" + invoice.number.replace("/", "") + "_%Y%m%d%H%M",
                time.localtime(time.time()),
            )
            data[filename] = []
            _logger.info("Factura %s" % (str(invoice.id)))
            CAB = {"lineId": "INVOIC_D_93A_UN_EAN007"}
            data[filename].append(edi._create_line_csv(CAB, structs))
            INV = {
                "lineId": "INV",
                "col1": invoice.number,
                "col2": invoice.type == "out_invoice" and "380" or "381",
                "col3": "9",
            }
            data[filename].append(edi._create_line_csv(INV, structs))
            DTM = {
                "lineId": "DTM",
                "col1": invoice.date_invoice.replace("-", ""),
            }
            data[filename].append(edi._create_line_csv(DTM, structs))
            if invoice.payment_mode_id and invoice.payment_mode_id.edi_code:
                PAI = {
                    "lineId": "PAI",
                    "col1": invoice.payment_mode_id.edi_code,
                }
                data[filename].append(edi._create_line_csv(PAI, structs))
            if invoice.type == "out_refund" and invoice.origin_invoices_ids:
                RFF = {
                    "lineId": "RFF",
                    "col1": "IV",
                    "col2": invoice.type == "out_refund"
                    and invoice.origin_invoices_ids,
                }
                data[filename].append(edi._create_line_csv(RFF, structs))
            elif invoice.type == "out_invoice" and invoice.name:
                RFF = {"lineId": "RFF", "col1": "ON", "col2": invoice.name}
                data[filename].append(edi._create_line_csv(RFF, structs))
            if invoice.picking_ids:
                for picking in invoice.picking_ids:
                    RFF = {
                        "lineId": "RFF",
                        "col1": "DQ",
                        "col2": picking.name,
                        "col3": datetime.strptime(
                            picking.date_done, "%Y-%m-%d %H:%M:%S"
                        ).strftime("%Y%m%d"),
                    }
                    data[filename].append(edi._create_line_csv(RFF, structs))
            NADSCO = {
                "lineId": "NADSCO",
                "col1": invoice.company_id.partner_id.gln,
                "col2": invoice.company_id.name,
                "col3": invoice.company_id.partner_id.edi_mercantil,
                "col4": invoice.company_id.street or " ",
                "col5": invoice.company_id.city[:35] or " ",
                "col6": invoice.company_id.zip or " ",
                "col7": invoice.company_id.vat or " ",
            }
            data[filename].append(edi._create_line_csv(NADSCO, structs))
            NADSU = {
                "lineId": "NADSU",
                "col1": invoice.company_id.partner_id.gln,
                "col2": invoice.company_id.name,
                "col3": invoice.company_id.partner_id.edi_mercantil,
                "col4": invoice.company_id.street or " ",
                "col5": invoice.company_id.city[:35] or " ",
                "col6": invoice.company_id.zip or " ",
                "col7": invoice.company_id.vat or " ",
            }
            data[filename].append(edi._create_line_csv(NADSU, structs))
            if invoice.partner_id.commercial_partner_id.no_commercial_nadbco:
                customer_nad = invoice.customer_order
            else:
                customer_nad = invoice.partner_id.commercial_partner_id
            FACT = {
                "lineId": "NADBCO",
                "col1": customer_nad.gln,
                "col2": customer_nad.name,
                "col3": customer_nad.street or " ",
                "col4": customer_nad.city[:35] or " ",
                "col5": customer_nad.zip or " ",
                "col6": customer_nad.vat or " ",
            }
            data[filename].append(edi._create_line_csv(FACT, structs))
            FACT = {
                "lineId": "NADBY",
                "col1": customer_nad.gln,
                "col2": customer_nad.name,
                "col3": customer_nad.street or " ",
                "col4": customer_nad.city[:35] or " ",
                "col5": customer_nad.zip or " ",
                "col6": customer_nad.vat or " ",
                "col7": invoice.customer_department or "",
            }
            data[filename].append(edi._create_line_csv(FACT, structs))
            NADII = {
                "lineId": "NADII",
                "col1": invoice.company_id.partner_id.gln,
                "col2": invoice.company_id.name,
                "col3": invoice.company_id.street or " ",
                "col4": invoice.company_id.city[:35] or " ",
                "col5": invoice.company_id.zip or " ",
                "col6": invoice.company_id.vat or " ",
            }
            data[filename].append(edi._create_line_csv(NADII, structs))
            FACT["lineId"] = "NADIV"
            FACT.pop('col7')
            data[filename].append(edi._create_line_csv(FACT, structs))
            NADDP = {
                "lineId": "NADDP",
                "col1": invoice.partner_shipping_id.gln,
                "col2": invoice.partner_shipping_id.name,
                "col3": invoice.partner_shipping_id.street or " ",
                "col4": invoice.partner_shipping_id.city[:35] or " ",
                "col5": invoice.partner_shipping_id.zip or " ",
            }
            data[filename].append(edi._create_line_csv(NADDP, structs))
            if invoice.customer_payer:
                NADPR = {
                    "lineId": "NADPR",
                    "col1": invoice.customer_payer.gln,
                    "col2": invoice.customer_payer.name,
                    "col3": invoice.customer_payer.street or " ",
                    "col4": invoice.customer_payer.city[:35] or " ",
                    "col5": invoice.customer_payer.zip or " ",
                }
                data[filename].append(edi._create_line_csv(NADPR, structs))
            NADPE = {
                "lineId": "NADPE",
                "col1": invoice.company_id.partner_id.gln,
            }
            data[filename].append(edi._create_line_csv(NADPE, structs))
            CUX = {
                "lineId": "CUX",
                "col1": invoice.currency_id.name,
                "col2": "4",
            }
            data[filename].append(edi._create_line_csv(CUX, structs))
            expiration_dates = invoice._get_date_due_list()
            if len(expiration_dates) == 1:
                mod = 35
            else:
                mod = 21
            for expiration_date in expiration_dates:
                PAT = {
                    "lineId": "PAT",
                    "col1": mod,
                    "col2": expiration_date[0],
                    "col3": expiration_date[1],
                }
                data[filename].append(edi._create_line_csv(PAT, structs))
            fin_seq = 1
            if invoice.commercial_discount_amount > 0.0:
                fin_seq = 2
                ALC = {
                    "lineId": "ALC",
                    "col1": "A",
                    "col2": "1",
                    "col3": "TD",
                    "col4": invoice.commercial_discount_input,
                    "col5": invoice.commercial_discount_amount,
                }
                data[filename].append(edi._create_line_csv(ALC, structs))
            if invoice.financial_discount_amount > 0.0:

                ALC = {
                    "lineId": "ALC",
                    "col1": "A",
                    "col2": str(fin_seq),
                    "col3": "TD",
                    "col4": invoice.financial_discount_input,
                    "col5": invoice.financial_discount_amount,
                }
                data[filename].append(edi._create_line_csv(ALC, structs))
            for line in invoice.invoice_line:
                if (
                    line.product_id
                    in invoice.partner_id.commercial_partner_id.remove_products
                ):
                    continue
                if not line.product_id.ean13:
                    raise exceptions.Warning(
                        _("EAN Error"),
                        _("The product %s not has an EAN") % line.product_id.name,
                    )
                LIN = {
                    "lineId": "LIN",
                    "col1": line.product_id.ean13 or "",
                    "col2": "EN",
                }
                data[filename].append(edi._create_line_csv(LIN, structs))
                if line.lot_id:
                    PIALIN = {
                        "lineId": "PIALIN",
                        "col1": "",
                        "col2": "",
                        "col3": "",
                        "col4": "",
                        "col5": line.lot_id.name,
                        "col6": "",
                        "col7": "",
                        "col8": "",
                    }
                    data[filename].append(edi._create_line_csv(PIALIN, structs))
                IMDLIN = {
                    "lineId": "IMDLIN",
                    "col1": line.name and line.name[:70] or "",
                    "col2": "M",
                    "col3": "F",
                }
                data[filename].append(edi._create_line_csv(IMDLIN, structs))
                QTYLIN = {
                    "lineId": "QTYLIN",
                    "col1": "47",
                    "col2": line.quantity,
                    "col3": line.uos_id.edi_code or "PCE",
                }
                data[filename].append(edi._create_line_csv(QTYLIN, structs))
                MOALIN = {"lineId": "MOALIN", "col1": line.price_subtotal}
                data[filename].append(edi._create_line_csv(MOALIN, structs))
                PRILIN = {
                    "lineId": "PRILIN",
                    "col1": "AAA",
                    "col2": line.price_unit * (1 - ((line.discount or 0.0) / 100.0)),
                    "col3": line.uos_id.edi_code or "PCE",
                }
                data[filename].append(edi._create_line_csv(PRILIN, structs))
                PRILIN = {
                    "lineId": "PRILIN",
                    "col1": "AAB",
                    "col2": line.price_unit,
                    "col3": line.uos_id.edi_code or "PCE",
                }
                data[filename].append(edi._create_line_csv(PRILIN, structs))
                for tax in line.invoice_line_tax_id:
                    TAXLIN = {
                        "lineId": "TAXLIN",
                        "col1": "VAT",
                        "col2": round(tax.amount * 100.0),
                        "col3": line.price_subtotal * tax.amount,
                    }
                    data[filename].append(edi._create_line_csv(TAXLIN, structs))
                if line.discount:
                    ALCLIN = {
                        "lineId": "ALCLIN",
                        "col1": "A",
                        "col2": "1",
                        "col3": "TD",
                        "col4": "",
                        "col5": line.discount,
                        "col6": line.discounted_amount,
                    }
                    data[filename].append(edi._create_line_csv(ALCLIN, structs))
            CNTRES = {"lineId": "CNTRES", "col1": "2"}
            data[filename].append(edi._create_line_csv(CNTRES, structs))
            MOARES = {
                "lineId": "MOARES",
                "col1": invoice.amount_untaxed,
                "col2": sum([x.price_unit * x.quantity for x in invoice.invoice_line]),
                "col3": invoice.amount_untaxed,
                "col4": invoice.amount_total,
                "col5": invoice.amount_tax,
            }
            data[filename].append(edi._create_line_csv(MOARES, structs))
            for tax in invoice.tax_line:
                if tax.base != 0.0:
                    TAXRES = {
                        "lineId": "TAXRES",
                        "col1": "VAT",
                        "col2": int(round((tax.amount / tax.base) * 100.0)),
                        "col3": tax.amount,
                        "col4": tax.base,
                    }
                else:
                    TAXRES = {
                        "lineId": "TAXRES",
                        "col1": "VAT",
                        "col2": 0,
                        "col3": tax.amount,
                        "col4": tax.base,
                    }
                data[filename].append(edi._create_line_csv(TAXRES, structs))
            context["model_log"] = "account.invoice"
            context["id_log"] = invoice.id
            context["filename"] = filename
            self.pool.get("edi.edi")._log(cr, uid, [edi.id], context)
            data[filename] = self.make_partner_changes(
                invoice.partner_id.commercial_partner_id,
                data[filename],
                "invoic",
            )
            return data

    def parse_desadv(self, cr, uid, edi, data, context, _logger, structs):
        def _create_line_desadv(data, filename, edi, sscc=None):
            operations = sscc.mapped("operation_ids")
            if sscc.type == "1":
                operations = sscc.mapped("child_ids.operation_ids")
            for line in operations:
                for move_id in line.mapped("linked_move_operation_ids.move_id"):
                    LIN = {
                        "lineId": "LIN",
                        "col1": line.product_id.ean13,
                        "col2": "EN",
                    }
                    data[filename].append(edi._create_line_csv(LIN, structs))
                    customer_reference = line.product_id.get_customer_info(
                        pick.partner_id.commercial_partner_id.id
                    )
                    gtin_number = None
                    if pick.partner_id.commercial_partner_id.desadv_use_gtin:
                        gtin_number = line.product_id.get_gtin14(
                            pick.partner_id.commercial_partner_id.id
                        )
                    if customer_reference or gtin_number:
                        PIALIN = {
                            "lineId": "PIALIN",
                            "col1": customer_reference or '',
                            "col2": "",
                            "col3": "",
                            "col4": gtin_number or '',
                            "col5": "",
                            "col6": "",
                            "col7": "",
                            "col8": "",
                            "col9": line.lot_id.name,
                        }
                        data[filename].append(edi._create_line_csv(PIALIN, structs))
                    IMDLIN = {
                        "lineId": "IMDLIN",
                        "col1": "F",
                        "col2": line.product_id.name,
                    }
                    data[filename].append(edi._create_line_csv(IMDLIN, structs))
                    QTYLIN = {
                        "lineId": "QTYLIN",
                        "col1": "12",
                        "col2": line.get_package_qty(sscc.type, move_id),
                        "col3": line.product_uom_id.edi_code or "PCE",
                    }
                    data[filename].append(edi._create_line_csv(QTYLIN, structs))
                    if pick.partner_id.commercial_partner_id.desadv_without_box_sscc:
                        complete_qty = line.product_id. \
                            gtin14_partner_specific_units(pick.partner_id)
                        QTYLIN = {
                            "lineId": "QTYLIN",
                            "col1": "59",
                            "col2": int(complete_qty),
                        }
                        data[filename].append(edi._create_line_csv(QTYLIN, structs))
                        FTXLIN = {
                            "lineId": "FTXLIN",
                            "col1": "AAA",
                            "col2": "Coincide con albaran {}".format(pick.name),
                        }
                        data[filename].append(edi._create_line_csv(FTXLIN, structs))
                    if not pick.partner_id.commercial_partner_id.desadv_without_box_sscc:
                        MOALIN = {
                            "lineId": "MOALIN",
                            "col1": str(move_id.price_subtotal_gross),
                            "col2": str(move_id.price_subtotal),
                            "col3": str(move_id.price_total),
                        }
                        data[filename].append(edi._create_line_csv(MOALIN, structs))

                        LOCLIN = {"lineId": "LOCLIN", "col1": pick.partner_id.gln}
                        data[filename].append(edi._create_line_csv(LOCLIN, structs))
                    PCILIN = {
                        "lineId": "PCILIN",
                        "col1": "36E",
                        "col2": (
                            pick.partner_id.use_date_as_life_date
                            or pick.partner_id.commercial_partner_id.use_date_as_life_date
                        )
                        and line.lot_id.use_date
                        and line.lot_id.use_date.split(" ")[0].replace("-", "")
                        or "",
                        "col3": (
                            not pick.partner_id.use_date_as_life_date
                            and not pick.partner_id.commercial_partner_id.use_date_as_life_date
                        )
                        and line.lot_id.use_date
                        and line.lot_id.use_date.split(" ")[0].replace("-", "")
                        or "",
                        "col4": "",
                        "col5": "",
                        "col6": "",
                        "col7": "",
                        "col8": line.lot_id.name,
                    }
                    data[filename].append(edi._create_line_csv(PCILIN, structs))

        pick_obj = self.pool.get("stock.picking")
        context["model_log"] = "stock.picking"
        context["ids_log"] = context["active_ids"]
        for pick in pick_obj.browse(cr, uid, context["active_ids"], context):
            if not pick.partner_id.gln:
                raise exceptions.Warning(
                    _("GLN Error"),
                    _("The partner %s does not have GLN configured")
                    % pick.partner_id.name,
                )
            if not pick.partner_id.commercial_partner_id.gln:
                raise exceptions.Warning(
                    _("GLN Error"),
                    _("The partner %s does not have GLN configured")
                    % pick.partner_id.commercial_partner_id.name,
                )
            if not pick.company_id.partner_id.gln:
                raise exceptions.Warning(
                    _("GLN Error"),
                    _("The partner %s does not have GLN configured")
                    % pick.company_id.partner_id.name,
                )
            filename = time.strftime(
                "ALB_"
                + pick.name.replace("/", "").replace("\\", "").replace(" ", "")
                + "_%Y%m%d%H%M",
                time.localtime(time.time()),
            )
            data[filename] = []
            _logger.info("Albaran %s" % (str(pick.id)))
            CAB = {"lineId": "DESADV_D_96A_UN_EAN005"}
            data[filename].append(edi._create_line_csv(CAB, structs))
            pick_name = pick.name
            if pick.partner_id.commercial_partner_id.desadv_only_numeric_ref:
                pick_name = pick_name.split('\\')[-1]
            BGM = {
                "lineId": "BGM",
                "col1": pick_name,
                "col2": "351",
                "col3": "9",
            }
            data[filename].append(edi._create_line_csv(BGM, structs))
            DTM = {
                "lineId": "DTM",
                "col1": time.strftime("%Y%m%d"),
                "col2": (pick.sale_id.top_date or pick.min_date)
                .split(" ")[0]
                .replace("-", ""),
            }
            data[filename].append(edi._create_line_csv(DTM, structs))
            if pick.partner_id.commercial_partner_id.desadv_without_box_sscc:
                ALI = {"lineId": "ALI", "col1": "X6"}
            else:
                ALI = {"lineId": "ALI", "col1": "X7"}
            data[filename].append(edi._create_line_csv(ALI, structs))
            if not pick.partner_id.commercial_partner_id.desadv_without_box_sscc:
                MOA = {
                    "lineId": "MOA",
                    "col1": str(pick.amount_gross),
                    "col2": str(pick.amount_untaxed),
                }
                data[filename].append(edi._create_line_csv(MOA, structs))

            RFF = {
                "lineId": "RFF",
                "col1": "ON",
                "col2": pick.sale_id.client_order_ref,
            }
            data[filename].append(edi._create_line_csv(RFF, structs))

            NADMS = {"lineId": "NADMS", "col1": pick.company_id.partner_id.gln}
            data[filename].append(edi._create_line_csv(NADMS, structs))
            NADMR = {
                "lineId": "NADMR",
                "col1": pick.sale_id.customer_transmitter.gln or pick.sale_id.partner_id.commercial_partner_id.gln,
            }
            data[filename].append(edi._create_line_csv(NADMR, structs))
            NADBY = {
                "lineId": "NADBY",
                "col1": pick.sale_id.partner_id.gln,
                "col2": "",
                "col3": pick.sale_id.customer_department or ""
            }
            if pick.partner_id.commercial_partner_id.desadv_without_box_sscc:
                NADBY['col2'] = '9'
            data[filename].append(edi._create_line_csv(NADBY, structs))
            NADSU = {"lineId": "NADSU", "col1": pick.company_id.partner_id.gln}
            data[filename].append(edi._create_line_csv(NADSU, structs))
            NADDP = {"lineId": "NADDP", "col1": pick.partner_id.gln}
            data[filename].append(edi._create_line_csv(NADDP, structs))
            CPS = {"lineId": "CPS", "col1": 1}
            data[filename].append(edi._create_line_csv(CPS, structs))
            if pick.partner_id.commercial_partner_id.desadv_without_box_sscc:
                PAC = {"lineId": "PAC", "col1": 1}
                data[filename].append(edi._create_line_csv(PAC, structs))

            # Se recorren las operaciones ya que contienen los datos de empaquetado.
            curr_parent = 1
            curr_cps = 2
            sscc_lines = [
                x for x in pick.mapped("pack_operation_ids.sscc_ids") if x.type == "1"
            ]
            if not sscc_lines:
                for sscc in pick.mapped("pack_operation_ids.sscc_ids"):
                    CPS = {
                        "lineId": "CPS",
                        "col1": curr_cps,
                        "col2": curr_parent,
                    }
                    curr_cps += 1
                    data[filename].append(edi._create_line_csv(CPS, structs))

                    PAC = {"lineId": "PAC", "col1": 1, "col2": "CT"}
                    data[filename].append(edi._create_line_csv(PAC, structs))
                    PCI = {
                        "lineId": "PCI",
                        "col1": "33E",
                        "col2": "BJ",
                        "col3": sscc.name,
                    }
                    data[filename].append(edi._create_line_csv(PCI, structs))
                    _create_line_desadv(data, filename, edi, sscc)
            for sscc in sscc_lines:
                CPS = {"lineId": "CPS", "col1": curr_cps, "col2": 1}
                curr_parent = curr_cps
                curr_cps += 1
                data[filename].append(edi._create_line_csv(CPS, structs))

                PAC = {
                    "lineId": "PAC",
                    "col1": pick.partner_id.commercial_partner_id.desadv_without_box_sscc and 1 or len(sscc.child_ids),
                    "col2": "201",
                }
                data[filename].append(edi._create_line_csv(PAC, structs))
                PCI = {
                    "lineId": "PCI",
                    "col1": "33E",
                    "col2": "BJ",
                    "col3": sscc.name,
                }
                data[filename].append(edi._create_line_csv(PCI, structs))
                if pick.partner_id.commercial_partner_id.desadv_without_box_sscc:
                    _create_line_desadv(data, filename, edi, sscc)
                else:
                    for sscc_child in sscc.child_ids:
                        CPS = {
                            "lineId": "CPS",
                            "col1": curr_cps,
                            "col2": curr_parent,
                        }
                        curr_cps += 1
                        data[filename].append(edi._create_line_csv(CPS, structs))

                        PAC = {"lineId": "PAC", "col1": 1, "col2": "CT"}
                        data[filename].append(edi._create_line_csv(PAC, structs))
                        PCI = {
                            "lineId": "PCI",
                            "col1": "33E",
                            "col2": "BJ",
                            "col3": sscc_child.name,
                        }
                        data[filename].append(edi._create_line_csv(PCI, structs))
                        _create_line_desadv(data, filename, edi, sscc_child)

            CNTRES = {
                "lineId": "CNTRES",
                "col1": int(sum([x.product_uom_qty for x in pick.move_lines])),
                "col2": pick.weight,
                "col3": len(pick.move_lines),
                "col4": pick.number_of_packages or "",
                "col5": pick.weight_net,
            }
            if pick.partner_id.commercial_partner_id.desadv_without_box_sscc:
                CNTRES['col2'] = ''
                CNTRES.pop('col4')
                CNTRES.pop('col5')
            data[filename].append(edi._create_line_csv(CNTRES, structs))
            context["model_log"] = "stock.picking"
            context["id_log"] = pick.id
            context["filename"] = filename
            self.pool.get("edi.edi")._log(cr, uid, [edi.id], context)
            data[filename] = self.make_partner_changes(
                pick.partner_id.commercial_partner_id, data[filename], "desadv"
            )
            return data

    def parse_recadv(self, cr, uid, edi, data, filename):
        pick_obj = self.pool.get("stock.picking")
        move_obj = self.pool.get("stock.move")
        partner_obj = self.pool.get("res.partner")
        product_obj = self.pool.get("product.product")
        uom_obj = self.pool.get("product.uom")
        vals = {}
        old_pick_id = False
        new_pick_id = False
        possible_move_ids = []
        visited_moves = []
        return_moves = []
        for line in data[filename]:
            if line and line[0] == "BGM":
                vals = {}
                vals["origin"] = line[1]["numdoc"]
            elif line and line[0] == "DTM":
                vals["date"] = (
                    line[1]["date"]
                    and datetime.strftime(
                        datetime.strptime(line[1]["date"], "%Y%m%d"),
                        "%Y-%m-%d %H:%M:%S",
                    )
                    or time.strftime("%Y-%m-%d %H:%M:%S")
                )
                vals["min_date"] = (
                    line[1]["min_date"]
                    and datetime.strftime(
                        datetime.strptime(line[1]["min_date"], "%Y%m%d"),
                        "%Y-%m-%d %H:%M:%S",
                    )
                    or time.strftime("%Y-%m-%d %H:%M:%S")
                )
            elif line and line[0] == "RFF":
                old_pick_id = pick_obj.search(cr, uid, [("name", "=", line[1]["ref"])])
                if not old_pick_id:
                    raise Exception(
                        "No se ha encontrado el albarán referenciado %s"
                        % line[1]["ref"]
                    )
                else:
                    old_pick_id = old_pick_id[0]
            elif line and line[0] == "NADMS":
                partner_id = partner_obj.search(
                    cr, uid, [("gln", "=", line[1]["emisor"])]
                )
                if not partner_id:
                    raise Exception(
                        "El emisor con gln %s no se ha encontrado" % (line[1]["emisor"])
                    )
                else:
                    vals["partner_id"] = partner_id[0]
            elif line and line[0] == "NADDP":
                partner_id = partner_obj.search(
                    cr, uid, [("gln", "=", line[1]["destino"])]
                )
                if not partner_id:
                    raise Exception(
                        "El destinatario con gln %s no se ha encontrado"
                        % (line[1]["destino"])
                    )
                else:
                    vals["partner_id"] = partner_id[0]
            elif line and "LIN" in line[0]:
                if line[0] == "LIN":
                    possible_move_ids = move_obj.search(
                        cr,
                        uid,
                        [
                            ("picking_id", "=", old_pick_id),
                            ("product_id.ean13", "=", line[1]["ean13"][:13]),
                            ("id", "not in", visited_moves),
                        ],
                    )
                    if not possible_move_ids:
                        raise Exception(
                            "No se ha encontrado el producto con ean13 %s en el albaran con id %s"
                            % (line[1]["ean13"][:13], old_pick_id)
                        )
                elif line[0] == "QTYLIN" and possible_move_ids:
                    move = False
                    for pos_move in move_obj.browse(cr, uid, possible_move_ids):
                        if pos_move.product_uom_qty == float(line[1]["enviadas"]):
                            visited_moves.append(pos_move.id)
                            move = pos_move
                            break
                    if move.product_uom_qty != float(line[1]["aceptadas"]):
                        return_moves.append(
                            (
                                move,
                                move.product_uom_qty - float(line[1]["aceptadas"]),
                            )
                        )
        if return_moves:
            return_wzd = self.pool.get("stock.return.picking").create(
                cr, uid, {"invoice_state": "2binvoiced"}
            )
            for move_data in return_moves:
                self.pool.get("stock.return.picking.line").create(
                    cr,
                    uid,
                    {
                        "product_id": move_data[0].product_id.id,
                        "quantity": move_data[1],
                        "wizard_id": return_wzd,
                        "move_id": move_data[0].id,
                    },
                )
            return_view = self.pool.get("stock.return.picking").create_returns(
                cr,
                uid,
                [return_wzd],
                {"active_ids": [old_pick_id], "active_id": old_pick_id},
            )
            new_pick_id = eval(return_view["domain"])[0][2]
            pick_obj.write(cr, uid, new_pick_id, vals)

    def parse_order(self, cr, uid, edi, data, filename):
        sale_obj = self.pool.get("sale.order")
        sale_line_obj = self.pool.get("sale.order.line")
        partner_obj = self.pool.get("res.partner")
        pay_mode_obj = self.pool.get("payment.mode")
        product_obj = self.pool.get("product.product")
        uom_obj = self.pool.get("product.uom")
        fpos_obj = self.pool.get("account.fiscal.position")
        sale_channel = self.pool.get("sale.channel")
        sale_ok = False
        old_sale_id = False
        new_sale_id = False
        line_vals = {}
        commercial_discount = 0.0
        early_payment_discount = 0.0
        for line in data[filename]:
            if line and line[0] == "ORD":
                vals = {}
                old_sale_id = False
                new_sale_id = False
                ref = line[1]["numdoc"]
                if line[1]["function"] == "5":
                    old_sale_id = sale_obj.search(
                        cr, uid, [("client_order_ref", "=", ref)]
                    )
                if line[1]["type"] == "224":
                    vals["urgent"] = True
                vals["client_order_ref"] = ref
                vals["note"] = ""
                vals["sale_channel_id"] = sale_channel.search(
                    cr, uid, [("name", "=", "EDI")]
                )[0]
            if line and line[0] == "DTM":
                if line[1]["document_date"] and len(line[1]["document_date"]) == 12:
                    vals["date_order"] = (
                        line[1]["document_date"]
                        and datetime.strftime(
                            datetime.strptime(line[1]["document_date"], "%Y%m%d%H%M"),
                            "%Y-%m-%d %H:%M",
                        )
                        or time.strftime("%Y-%m-%d %H:%M:%S")
                    )
                else:
                    vals["date_order"] = (
                        line[1]["document_date"]
                        and datetime.strftime(
                            datetime.strptime(line[1]["document_date"], "%Y%m%d"),
                            "%Y-%m-%d",
                        )
                        or time.strftime("%Y-%m-%d")
                    )
                if line[1]["document_date"] and len(line[1]["document_date"]) == 12:
                    vals["top_date"] = (
                        line[1]["limit_date"]
                        and datetime.strftime(
                            datetime.strptime(line[1]["limit_date"], "%Y%m%d%H%M"),
                            "%Y-%m-%d",
                        )
                        or False
                    )
                else:
                    vals["top_date"] = (
                        line[1]["limit_date"]
                        and datetime.strftime(
                            datetime.strptime(line[1]["limit_date"], "%Y%m%d"),
                            "%Y-%m-%d",
                        )
                        or False
                    )

            if line and line[0] == "PAI" and line[1]["fpago"]:
                payment_mode = pay_mode_obj.search(
                    cr, uid, [("edi_code", "=", line[1]["fpago"])]
                )
                if payment_mode:
                    vals["payment_mode_id"] = payment_mode and payment_mode[0] or False
            if line and (
                (line[0] == "ALI" and line[1]["info"])
                or (line[0] == "FTX" and line[1]["texto"])
            ):
                vals["note"] += line[0] == "ALI" and line[1]["info"] or line[1]["texto"]
            if line and line[0] == "RFF":
                vals["season"] = line[1]["temp"]
                vals["customer_department"] = line[1]["cod"]
            if line and line[0] == "NADMS":
                partner_id = partner_obj.search(
                    cr, uid, [("gln", "=", line[1]["emisor"])]
                )
                if not partner_id:
                    raise Exception(
                        "El cliente con gln %s no se ha encontrado"
                        % (line[1]["emisor"])
                    )
                else:
                    vals["customer_transmitter"] = partner_id[0]
            if line and line[0] == "NADPR":
                partner_id = partner_obj.search(
                    cr, uid, [("gln", "=", line[1]["emisorPago"])]
                )
                if not partner_id:
                    raise Exception(
                        "El cliente con gln %s no se ha encontrado"
                        % (line[1]["emisorPago"])
                    )
                else:
                    vals["customer_payer"] = partner_id[0]
            if line and line[0] == "NADSU":
                partner_id = partner_obj.search(
                    cr, uid, [("gln", "=", line[1]["comp"])]
                )
                if not partner_id:
                    raise Exception(
                        "El partner con gln %s no se ha encontrado" % (line[1]["comp"])
                    )
                else:
                    partner = partner_obj.browse(cr, uid, partner_id)
                    vals["company_id"] = partner.company_id.id
                    warehouse_ids = self.pool.get("stock.warehouse").search(
                        cr, uid, [("company_id", "=", partner.company_id.id)]
                    )
                    if warehouse_ids:
                        vals["warehouse_id"] = warehouse_ids[0]
            if line and line[0] == "NADBY":
                partner_id = partner_obj.search(
                    cr, uid, [("gln", "=", line[1]["comprador"])]
                )
                if not partner_id:
                    raise Exception(
                        "El comprador con gln %s no se ha encontrado"
                        % (line[1]["comprador"])
                    )
                else:
                    partner = partner_obj.browse(cr, uid, partner_id)
                    vals["customer_branch"] = line[1]["sucursal"]
                    vals["partner_invoice_id"] = partner_id[0]
                    vals["partner_id"] = partner.id
                    partner = partner_obj.browse(cr, uid, partner_id[0])
                    vals["pricelist_id"] = partner.property_product_pricelist.id
                    vals["fiscal_position"] = partner.property_account_position.id
                    # creo que hace falta
                    vals_fiscal_position = partner.property_account_position
                    if not vals.get("payment_mode_id", False):
                        vals["payment_mode_id"] = partner.customer_payment_mode.id
                    vals["payment_term"] = partner.property_payment_term.id
            if line and line[0] == "NADDP":
                partner_id = partner_obj.search(
                    cr, uid, [("gln", "=", line[1]["destino"])]
                )
                if not partner_id:
                    raise Exception(
                        "El destinatario con gln %s no se ha encontrado"
                        % (line[1]["destino"])
                    )
                else:
                    vals["partner_shipping_id"] = partner_id[0]
            if line and line[0] == "CNTRES":
                vals["total_packages"] = line[1]["bultos"]
            if line and line[0] == "NADIV":
                partner_id = partner_obj.search(
                    cr, uid, [("gln", "=", line[1]["emisor"])]
                )
                if not partner_id:
                    raise Exception(
                        "El emisor con gln %s no se ha encontrado" % (line[1]["emisor"])
                    )
                else:
                    vals["partner_invoice_id"] = partner_id[0]
                    partner = partner_obj.browse(cr, uid, partner_id[0])
                    vals["pricelist_id"] = partner.property_product_pricelist.id
                    vals["fiscal_position"] = partner.property_account_position.id
                    # creo que hace falta
                    vals_fiscal_position = partner.property_account_position
                    if not vals.get("payment_mode_id", False):
                        vals["payment_mode_id"] = partner.customer_payment_mode.id
                    vals["payment_term"] = partner.property_payment_term.id
            if line and line[0] == "ALC":
                if line[1]["tipo"] == "EAB":
                    early_payment_discount = line[1]["porcentaje"]
                elif line[1]["tipo"] == "TD":
                    commercial_discount = line[1]["porcentaje"]
            if line and "LIN" in line[0]:
                if old_sale_id:
                    wf_service = netsvc.LocalService("workflow")
                    wf_service.trg_validate(
                        uid, "sale.order", old_sale_id[0], "cancel", cr
                    )
                    old_sale_id = False
                if not new_sale_id:
                    new_sale_id = sale_obj.create(cr, uid, vals)

                if line[0] == "LIN":
                    if line_vals:
                        line_vals["order_id"] = new_sale_id
                        # taxes = fpos_obj.map_tax(cr,uid,vals['fiscal_position'],product.taxes_id)
                        taxes = fpos_obj.map_tax(
                            cr, uid, vals_fiscal_position, product.taxes_id
                        )
                        line_vals["tax_id"] = [(6, 0, taxes)]
                        sale_line_obj.create(cr, uid, line_vals)
                        line_vals = {}
                        product = False
                    spain_country_id = self.pool.get(
                        "ir.model.data"
                    ).get_object_reference(cr, uid, "base", "es")[1]
                    product_id = product_obj.search(
                        cr,
                        uid,
                        [
                            ("ean13", "=", line[1]["ean13"][:13]),
                            "|",
                            ("country", "=", False),
                            ("country", "=", spain_country_id),
                        ],
                    )
                    if not product_id:
                        old_product_id = product_obj.search(
                            cr,
                            uid,
                            [
                                ("active", "=", False),
                                ("ean13", "=", line[1]["ean13"][:13]),
                                "|",
                                ("country", "=", False),
                                ("country", "=", spain_country_id),
                            ],
                        )
                        if not old_product_id:
                            raise Exception(
                                "El producto con ean13 %s no se ha encontrado"
                                % (line[1]["ean13"][:13])
                            )
                        else:
                            line_vals["product_id"] = product_obj.search(
                                cr, uid, [("default_code", "=", "FAOLG")]
                            )[0]
                    else:
                        line_vals["product_id"] = product_id[0]
                        product = product_obj.browse(cr, uid, product_id[0])
                elif line[0] == "PIALIN":
                    # si viene la referencia interna del cliente y no está guardada se crea
                    if line[1]["calificador"] == "IN" and "product_id" in line_vals:
                        if not product_obj.get_customer_info(
                            cr,
                            uid,
                            product.id,
                            partner.commercial_partner_id.id,
                        ):
                            product_obj.create_edi_customer_info(
                                cr,
                                uid,
                                product.id,
                                partner.commercial_partner_id.id,
                                line[1]["referencia"],
                            )

                elif line[0] == "IMDLIN" and line[1]["descripcion"] and line_vals:
                    if line_vals.get("name", False):
                        line_vals["name"] += u" " + line[1]["descripcion"]
                    else:
                        line_vals["name"] = line[1]["descripcion"]
                elif line[0] == "QTYLIN":
                    if line[1]["calificador"] == "21":
                        line_vals["product_uom_qty"] = line[1]["qty"]
                        line_vals["product_uos_qty"] = line[1]["qty"]
                        edi_code = line[1]["uom_code"] or "PCE"
                        uom_ids = uom_obj.search(cr, uid, [("edi_code", "=", edi_code)])
                        if not uom_ids:
                            raise Exception(
                                "La unidad de medida con codigo %s no se ha encontrado"
                                % (line[1]["uom_code"])
                            )
                        else:
                            line_vals["product_uom"] = uom_ids[0]
                            line_vals["product_uos"] = uom_ids[0]
                    elif line[1]["calificador"] == "59":
                        line_vals["units_per_package"] = line[1]["qty"]

                elif line[0] == "PRILIN" and line_vals and line[1]["tipo"] == "AAA":
                    if not line_vals.get("price_unit"):
                        if line[1]["precio"]:
                            line_vals["price_unit"] = line[1]["precio"]
                    if line[1]["precio"]:
                        line_vals["net_price"] = line[1]["precio"]

                elif line[0] == "PRILIN" and line_vals and line[1]["tipo"] == "AAB":
                    if line[1]["precio"]:
                        line_vals["price_unit"] = line[1]["precio"]
                        line_vals["brut_price"] = line[1]["precio"]
                    sale_obj.write(
                        cr,
                        uid,
                        new_sale_id,
                        {
                            "commercial_discount_input": commercial_discount,
                            "financial_discount_input": early_payment_discount,
                        },
                    )

        if line_vals:
            line_vals["order_id"] = new_sale_id
            # taxes = fpos_obj.map_tax(cr,uid,vals['fiscal_position'],product.taxes_id)
            product = product_obj.browse(cr, uid, line_vals["product_id"])
            taxes = fpos_obj.map_tax(cr, uid, vals_fiscal_position, product.taxes_id)
            line_vals["tax_id"] = [(6, 0, taxes)]
            sale_line_obj.create(cr, uid, line_vals)
        if new_sale_id:
            sale_obj.generate_discounts(cr, uid, new_sale_id)
            return sale_obj.browse(cr, uid, new_sale_id).name
