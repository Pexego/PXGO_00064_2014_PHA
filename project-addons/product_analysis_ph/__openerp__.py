# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Product analysis PH',
    'version': '1.0',
    'category': 'product',
    'description': """Inherits product_analysis module to extends it""",
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'product_analysis',
    ],
    'data': [
        'views/stock_lot_analysis_report.xml',
        'views/stock_view.xml',
        'views/product_analysis_view.xml',
    ],
    'installable': True
}
