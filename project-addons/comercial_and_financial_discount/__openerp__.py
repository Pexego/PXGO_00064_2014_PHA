# -*- coding: utf-8 -*-
#################################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2013 Julius Network Solutions SARL <contact@julius.fr>
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
    "name" : "Comercial and financial discount",
    "summary": "Comercial and financial discount on sale orders",
    "version" : "1",
    "author" : "Julius Network Solutions & Pharmadus",
    "website" : "http://www.pharmadus.com",
    "category" : "Sales Management",
    "depends" : [
        "sale",
        "stock",
        "account",
    ],
    "description": """
Comercial and financial discount on a sale order
================================================
Module to manage comercial and financial discounts in sale orders

This module will add two fields in the sale order, and it will work as the module "delivery" works.
    """,
    "demo" : [],
    "data" : [
        "views/sale_view.xml",
        "views/report_quotation_discounted.xml",
        "data/product_data.xml",
    ],
    'installable' : True,
    'active' : False,
}