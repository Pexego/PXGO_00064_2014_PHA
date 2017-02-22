# -*- encoding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2007-TODAY ASPerience SARL (<http://www.asperience.fr>).
#    All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
{
    "name": "ASPerience EDI",
    "version": "8.0",
    "author": "ASPerience",
    "website": "http://www.asperience.fr",
    "sequence": 0,
    "certificate": "",
    "license": "",
    "depends": ["board", "account_payment_sale", "sale",
                "commercial_and_financial_discount", "stock_picking_valued"],
    "category": "Generic Modules/EDI",
    "complexity": "easy",
    "description": """
Used for the communication with others proprietary ERP's.
Ability to import and export files in CSV,XML and EDI.
Shares in the background or not, with the possibility of planning by cron.
WARNING: folders tree and folders management is not fully secured. This must NOT be used by novice users
    """,
    "data": [
        "data/edi_data.xml",
        "security/edi_security.xml",
        "security/ir.model.access.csv",
        "views/edi.xml",
        "views/edi_board.xml",
        "views/edi_menu.xml",
        "views/stock.xml",
        "views/product.xml",
        "views/edi_fields_view.xml",
        "data/import_orders.xml",
        "data/export_invoic.xml",
        "data/export_desadv.xml",
        "data/import_recadv.xml",
        "wizard/export_edi_view.xml",
        "data/sscc_sequence.xml",
        "data/ir_cron.xml",
    ],
    "images": [
        "images/asperience.png",
        "images/1.png",
        "images/2.png",
        "images/3.png",
        "images/4.png",
        "images/5.png",
    ],
    "auto_install": False,
    "installable": True,
    "application": True,

}
