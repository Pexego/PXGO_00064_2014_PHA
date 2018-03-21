# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Copy from...',
    'version': '1.0',
    'author': 'Pharmadus I.T.',
    'summary' : 'Copy data from other record',
    'description': 'Copy data from other record',
    'category': 'General',
    'website': 'www.pharmadus.com',
    'depends' : [
        'base',
        'mrp',
        'product_analysis',
    ],
    'data' : [
        'views/mrp_bom_view.xml',
        'views/product_view.xml',
        'views/stock_production_lot_view.xml',
    ],
    'installable': True
}
