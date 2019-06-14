# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': '20 bananas Connector',
    'version': '8.0.1.0.0',
    'summary': 'Connect with 20 bananas API',
    'category': 'Connector',
    'author': 'comunitea',
    'maintainer': 'comunitea',
    'website': 'www.comunitea.com',
    'license': 'AGPL-3',
    'depends': [
        'connector',
        'sale',
        'sale_channel'
    ],
    'data': [
        'views/bananas_backend.xml',
        'views/res_partner.xml',
        'views/product_view.xml',
        'views/sale.xml',
        'data/ir_cron.xml',
        'data/sale_channel.xml',
        'security/ir.model.access.csv'
    ],
    'installable': True,
}
