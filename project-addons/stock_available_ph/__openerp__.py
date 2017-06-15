# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MRP stock available and production planning',
    'version': '3.1',
    'category': 'mrp',
    'summary' : ' Returns stock available and anticipates consumption of the next productions',
    'description': " //static/description/index.html//",
    'icon': '//static/src/img/icon.jpg//',
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'mrp',
        'stock',
        'custom_views',
        'custom_calendars',
        'product_stock_unsafety'
    ],
    'data': [
        'views/stock_view.xml',
        'views/production_planning_view.xml',
        'views/product_view.xml',
        'views/product_stock_unsafety_view.xml',
        'wizards/product_stock_by_day.xml',
        'wizards/bom_member_of.xml',
        'data/initialization.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
