# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class ProductQualityLimits(models.Model):
    _inherit = 'product.quality.limits'

    copy_from = fields.Many2one(string='Copy from...',
                                comodel_name='product.quality.limits')

    @api.multi
    def action_copy_from(self):
        self.ensure_one()
        if self.copy_from:
            origin = self.copy_from
            fields_to_copy = ('filter_tare', 'filter_gross_weight',
                'filter_min_action_weight','filter_min_alert_weight',
                'filter_max_alert_weight', 'filter_max_action_weight',
                'filter_av_min_action_weight', 'filter_av_min_alert_weight',
                'filter_av_max_alert_weight', 'filter_av_max_action_weight',
                'full_case_min_action_weight', 'full_case_min_alert_weight',
                'full_case_max_alert_weight', 'full_case_max_action_weight',
                'loc_samples', 'analysis', 'tu2', 'tu1', 'to1', 'to2')
            dict = {}
            for field in fields_to_copy:
                if field in origin._fields:
                    dict[field] = getattr(origin, field)
            self.update(dict)
        return self
