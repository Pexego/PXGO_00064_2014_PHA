# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Production customizations',
    'version': '8.0',
    'category': 'mrp',
    'summary' : 'MRP Production customizations',
    'description': "MRP Production customizations",
    'icon': '//static/src/img/icon.jpg//',
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends': [
        'mrp',
        'mrp_hoard',
        'quality_protocol_report',
    ],
    'data': [
        'views/mrp_production_view.xml',
        'views/mrp_routing_view.xml',
        'wizards/mrp_production_confirm_view.xml',
    ],
    'installable': True
}
