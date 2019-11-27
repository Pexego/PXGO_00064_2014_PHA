# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'MRP BoM - Export attachments',
    'version': '8.0.1.0.0',
    'license': 'AGPL-3',
    'author': 'Pharmadus I.T. Department',
    'website': 'https://www.pharmadus.com',
    'category': 'MRP',
    'depends': ['product_spec'],
    'data': [
        'wizard/export_wizard_view.xml',
        'data/ir_cron.xml',
    ],
    'installable': True,
}
