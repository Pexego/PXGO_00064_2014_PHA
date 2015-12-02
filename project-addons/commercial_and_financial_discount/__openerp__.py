# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 Pharmadus. All Rights Reserved
#    $Óscar Salvador <oscar.salvador@pharmadus.com$
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
#################################################################################

{
    "name" : "Commercial and financial discount",
    "summary": "Commercial and financial discount on orders",
    "version" : "1",
    "author" : "Pharmadus",
    "website" : "http://www.pharmadus.com",
    "category" : "Sales & Purchases Management",
    "depends" : [
        "sale",
        "stock",
        "account",
        "purchase",
        "purchase_discount",
    ],
    "description": """
Comercial and financial discount on orders
==========================================
Module to manage comercial and financial discounts in sale and purchase orders

This module will add commercial and financial discounts fields in sale and purchase order.
Both fields values can be preset in the partner form, assigning specific discounts to each partner.
The discounts only will be applied if the user press "Generate discounts" button in the order form.
    """,
    "data" : [
        "views/res_partner_view.xml",
        "views/sale_view.xml",
        "views/purchase_view.xml",
        "views/account_invoice_view.xml",
        "views/report_saleorder.xml",
        "views/report_invoice.xml",
    ],
    'installable' : True,
    'active' : False,
}