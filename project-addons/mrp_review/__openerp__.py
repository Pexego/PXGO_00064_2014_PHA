# -*- coding: utf-8 -*-
# © 2017 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': "MRP review",
    'version': '1.0',
    'category': 'production',
    'description': """Adds the state review on mrp.production.""",
    'author': 'Pexego Sistemas Informáticos',
    'website': 'www.pexego.es',
    "depends": ['mrp', 'mrp_hoard'],
    "data": ['security/mrp_review_security.xml',
             'mrp_workflow.xml',
             'views/mrp.xml',
             'views/product.xml',
            ],
    "installable": True
}
