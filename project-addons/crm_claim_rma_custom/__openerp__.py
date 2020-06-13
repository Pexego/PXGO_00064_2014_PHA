# -*- coding: utf-8 -*-
# © 2015 Comunitea
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Claims customizations',
    'version': '1.0',
    'category': 'sale',
    'description': """""",
    'author': 'Comunitea',
    'website': '',
    "depends": ['base', 'sale', 'crm_claim', 'crm_claim_rma', 'custom_views'],
    "data": [
        'views/crm_claim.xml',
        'views/crm_claim_stage.xml',
        'qweb_reports/crm_claim.xml',
        'claim_report.xml'
    ],
    "installable": True
}
