# -*- coding: utf-8 -*-
# © 2017 Comunitea & Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Stock transfer only available products (PHARMADUS)',
    'version': '1.1',
    'category': 'stock',
    'description': """Prevents transfer stock unavailable""",
    'author': 'Comunitea & Pharmadus I.T.',
    'website': '',
    "depends": ['stock'],
    "data": [
        'views/stock_view.xml',
        'wizard/stock_transfer_details.xml',
    ],
    "installable": True
}
