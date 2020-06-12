# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
{
    'name': 'Mail customizations for Pharmadus',
    'version': '1.0',
    'category': '',
    'summary' : 'Customizations of mail sending on purchases, sales, accounting...',
    'author': 'Pharmadus I.T.',
    'website': 'www.pharmadus.com',
    'depends' : [
        'base',
        'mail',
        'email_template',
        'sale',
        'purchase',
    ],
    'data' : [
        'security/ir.model.access.csv',
        'data/email_template.xml',
        'data/ir_cron.xml',
        'views/res_partner_view.xml',
        'views/res_company_view.xml',
        'views/purchase_order_view.xml',
        'views/sale_order_view.xml',
        'views/account_invoice_view.xml',
    ],
    'installable': True
}
