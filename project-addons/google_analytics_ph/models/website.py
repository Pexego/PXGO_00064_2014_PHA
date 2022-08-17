# -*- coding: utf-8 -*-
# © 2022 Pharmadus Botanicals
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class Website(models.Model):
    _inherit = 'website'

    ga4_ph_id = fields.Char('Google Analytics 4 (PH)')
    ga4_ph_script = fields.Char(compute='_compute_ga4_ph_script', store=True)

    @api.depends('ga4_ph_id')
    def _compute_ga4_ph_script(self):
        self.ga4_ph_script = """
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '%s');        
            """ % self.ga4_ph_id


class WebsiteConfig(models.Model):
    _inherit = 'website.config.settings'

    ga4_ph_id = fields.Char('Google Analytics 4 ID (PH)',
                            related='website_id.ga4_ph_id')
