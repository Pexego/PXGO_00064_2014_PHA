# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'EAN10 => EAN13 codes generator and usage view',
    'version': '8.0',
    'category': 'Products',
    'summary' : 'EAN10 => EAN13 codes generator and usage view',
    'description': "//static/description/index.html//",
    'icon': "ean10/static/description/icon.png",
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'product',
    ],
    'data': [
        'views/ean10_view.xml',
        'wizard/create_ean13_wizard.xml',
        'security/ir.model.access.csv',
    ],
    'qweb': ['static/src/xml/qweb.xml'],
    'installable': True
}
