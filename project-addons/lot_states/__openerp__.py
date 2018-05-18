# -*- coding: utf-8 -*-
# © 2014 Pexego
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Lot states',
    'version': '2.0',
    'category': 'stock',
    'description': """
        Se añaden los siguientes estados a los lotes: nuevo, en revision, revisado, aprobado, rechazado
        Se impide realizar un movimiento hasta que el lote no se encuentre en el estado apropiado

        Al rechazar el lote se crea un movimiento de la localizacion actual
        a rechazados. Desde rechazados existe la posibilidad de devolver el material al proveedor
        Se añade la posibilidad de consumir cuarentena en las producciones.

        """,
    'author': 'Pexego, Pharmadus I.T.',
    'website': 'www.pexego.es, www.pharmadus.com',
    'depends': [
        'base',
        'stock',
        'product_expiry',
        'mrp'
    ],
    'data': [
        'wizard/lot_reject_partial.xml',
        'wizard/lot_detail_wizard.xml',
        'views/lot_view.xml',
        'views/mrp_view.xml',
        'views/stock_view.xml',
        'data/lot_workflow.xml',
        'data/stock_location_data.xml',
        'data/remove_old_translations.xml',
        'security/ir.model.access.csv',
    ]
    ,
    'installable': True
}
