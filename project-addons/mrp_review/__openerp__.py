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
    "data": ['mrp_workflow.xml',
             'wizard/mrp_set_final_quantity.xml',
             'wizard/mrp_release_all.xml',
             'views/mrp.xml',
             'views/mrp_routing.xml',
            ],
    "installable": True
}
