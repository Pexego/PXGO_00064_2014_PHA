# -*- coding: utf-8 -*-
# © 2017 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class MrpProduction(models.Model):
    _inherit = 'mrp.production'

    next_lot = fields.Char(compute='_next_lot', readonly=True)

    @api.one
    def _next_lot(self):
        if self.product_id and self.product_id.sequence_id:
            sequence = self.product_id.sequence_id
        else:
            sequence = self.env.ref('stock.sequence_production_lots')

        if sequence:
            d = sequence._interpolation_dict()
            prefix = sequence.prefix and sequence.prefix % d or ''
            suffix = sequence.suffix and sequence.suffix % d or ''
            self.next_lot = prefix + '%%0%sd' % sequence.padding % \
                                     sequence.number_next_actual + suffix
        else:
            self.next_lot = False