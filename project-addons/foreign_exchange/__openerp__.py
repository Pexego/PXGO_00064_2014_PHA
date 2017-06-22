# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Foreign exchange',
    'version': '1.0',
    'category': '',
    'summary' : 'Shows exchange rates between currencies',
    'description': 'Shows exchange rates between currencies',
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends' : [
        'base',
        'account',
    ],
    'data' : [
        'views/foreign_exchange_view.xml',
    ],
    'installable': True
}
