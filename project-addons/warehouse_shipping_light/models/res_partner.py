# -*- coding: utf-8 -*-
from openerp import models, fields


class ResPartner(models.Model):
    _inherit = 'res.partner'

    # Las opciones de este selector también están definidas en stock.palet.report.selector
    # por lo que, si las cambiamos, tenemos que actualizarlas allí también
    palet_report_type = fields.Selection([
            ('standad', 'Estándar'),
            ('gs1-128-1', 'GS1-128 (02-37-15-10-00)')
        ],
        string='Tipo de etiquetas de palet',
        default='standard'
    )
