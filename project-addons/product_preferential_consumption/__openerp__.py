# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Product preferential consumption extra data',
    'version': '1.0',
    'category': 'mrp',
    'summary' : 'Computes preferential consumption date dependign on the option selected in duration type',
    'description': "Computes preferential consumption date dependign on the option selected in duration type",
    'icon': '',
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'product',
        'stock_available_ph'
    ],
    'data': [
        'views/product_view.xml',
        'views/stock_view.xml',
    ],
    'installable': True
}
