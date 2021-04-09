# -*- coding: utf-8 -*-
# © 2021 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Editable reports',
    'version': '1.0',
    'category': 'Reports',
    'description': "//static/description/index.html//",
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'base',
        'web',
        'stock',
    ],
    'data': [
        'security/ir.model.access.csv',
        'views/editable_report_view.xml',
        'views/stock_production_lot_view.xml',
        'reports/editable_report.xml',
        'reports/stock_lot_analysis.xml',
    ],
    'installable': True
}
