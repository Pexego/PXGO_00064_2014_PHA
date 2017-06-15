# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Check pricelist',
    'version': '1.0',
    'category': '',
    'summary' : 'Check pricelist, products prices, commercial/financial discounts and taxes of sale orders',
    'description': 'Add a button to sale order to check pricelist, products prices, commercial/financial discounts and taxes',
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends' : [
        'base',
        'sale',
        'commercial_and_financial_discount',
    ],
    'data' : [
        'views/sale_view.xml',
        'wizard/check_pricelist_view.xml',
    ],
    'installable': True
}
