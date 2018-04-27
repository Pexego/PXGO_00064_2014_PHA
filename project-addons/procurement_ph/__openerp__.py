# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Procurement PH',
    'version': '1.0',
    'category': 'stock',
    'description': """Inherits procurements calculations methods to wait for threads""",
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'procurement',
        'stock',
    ],
    'data': [
        'views/procurement_view.xml',
    ],
    'installable': True
}
