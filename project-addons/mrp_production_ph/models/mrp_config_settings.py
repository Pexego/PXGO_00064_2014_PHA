# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class MrpConfigSettings(models.Model):
    _inherit = 'mrp.config.settings'

    reprocessing_route_warning = fields.Char()

    @api.multi
    def set_reprocessing_route_warning(self):
        self.ensure_one()
        self.env['ir.config_parameter'].set_param('reprocessing_route_warning',
                                                  self.reprocessing_route_warning)

    def get_default_reprocessing_route_warning(self, cr, uid, fields, context=None):
        value = self.pool['ir.config_parameter'].\
            get_param(cr, uid, 'reprocessing_route_warning')
        res = {'reprocessing_route_warning': value}
        return res
