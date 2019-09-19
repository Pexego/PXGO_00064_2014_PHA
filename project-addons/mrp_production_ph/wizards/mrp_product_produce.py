# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class MrpProductProduce(models.TransientModel):
    _inherit = 'mrp.product.produce'

    tare = fields.Float()