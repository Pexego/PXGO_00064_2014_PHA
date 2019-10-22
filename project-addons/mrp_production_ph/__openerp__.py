# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MRP Production PH',
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
        'views/product_view.xml',
        'views/stock_view.xml',
        'views/res_config_view.xml',
        'wizards/mrp_production_confirm_view.xml',
        'wizards/mrp_production_use_lot_view.xml',
        'wizards/mrp_product_produce_view.xml',
        'wizards/stock_transfer_details_view.xml',
        'security/ir.model.access.csv',
    ],
    'installable': True
}
