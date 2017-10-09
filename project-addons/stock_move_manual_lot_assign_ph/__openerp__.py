# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    "name": "Stock move assign lots manual (Pharmadus)",
    "summary": "",
    "version": "8.0.1.0.0",
    "category": "Uncategorized",
    "website": "www.pharmadus.com",
    "author": "Pharmadus I.T.",
    "license": "AGPL-3",
    "application": False,
    "installable": True,
    "depends": [
        "stock_move_manual_lot_assign",
        "mrp_hoard",
        "custom_views",
    ],
    "data": [
        'views/stock_move_view.xml'
    ],
}
