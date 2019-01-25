# -*- coding: utf-8 -*-
# © 2019 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class L10nEsAeatMod347Report(models.Model):
    _inherit = "l10n.es.aeat.mod347.report"

    extended_partner_record_ids = fields.One2many(
        comodel_name='l10n.es.aeat.mod347.partner_record',
        inverse_name='report_id', string='Extended Partner Records')


class L10nEsAeatMod347PartnerRecord(models.Model):
    _inherit = 'l10n.es.aeat.mod347.partner_record'

    partner_ref = fields.Char(related='partner_id.ref', readonly=True)
    partner_comercial = fields.Char(related='partner_id.comercial',
                                    readonly=True)
    partner_street = fields.Char(related='partner_id.street', readonly=True)
    partner_street2 = fields.Char(related='partner_id.street2', readonly=True)
    partner_zip = fields.Char(related='partner_id.zip', readonly=True)
    partner_city = fields.Char(related='partner_id.city', readonly=True)
    partner_state_id = fields.Many2one(related='partner_id.state_id',
                                       readonly=True)
    partner_country_id = fields.Many2one(related='partner_id.country_id',
                                         readonly=True)
    partner_email = fields.Char(related='partner_id.email', readonly=True)

