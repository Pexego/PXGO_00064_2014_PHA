# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Sale wizards',
    'version': '1.0',
    'category': 'sale',
    'summary' : ' Sale wizards',
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'sale',
    ],
    'data': [
        'views/base_sale_wizards.xml',
        'views/sale_order_view.xml',
        'wizard/sale_from_line_subline.xml',
        'wizard/sale_from_catalog.xml',
        'wizard/sale_from_history.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
