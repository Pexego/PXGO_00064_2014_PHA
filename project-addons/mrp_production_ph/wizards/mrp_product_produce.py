# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class MrpProductProduce(models.TransientModel):
    _inherit = 'mrp.product.produce'

    tare = fields.Float()

    @api.multi
    def do_produce(self):
        res = super(MrpProductProduce, self).do_produce()
        production_id = self.env['mrp.production'].browse(
            self.env.context.get('active_id', False)
        )
        if production_id and self.tare:
            production_id.tare = self.tare
        return res