# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Lot tracking',
    'version': '1.0',
    'category': 'Warehouse',
    'summary' : 'Shows the paths that follow the lots of a product',
    'description': " //static/description/index.html//",
    'icon': '//static/src/img/icon.jpg//',
    'author': 'Pharmadus I.T. Department',
    'website': 'www.pharmadus.com',
    'depends': ['stock', 'quality_management_menu', 'custom_widths'],
    'data': [
        'data/remove_old_translations.xml',
        'views/lot_tracking_view.xml',
        'views/lot_tracking_productions_view.xml',
        'views/report_lot_tracking.xml',
        'views/report_lot_tracking_productions.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
