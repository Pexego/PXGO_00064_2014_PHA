# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': "Quants to picking",
    'version': '1.0',
    'category': '',
    'summary' : 'Choose some quants to create a new picking automatically',
    'description': " //static/description/index.html//",
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends' : [
        'stock',
    ],
    'data' : [
        'views/stock_view.xml',
        'wizard/quants_to_picking_wizard.xml',
    ],
    'qweb': ['static/src/xml/stock_quant.xml'],
    'installable': True
}
