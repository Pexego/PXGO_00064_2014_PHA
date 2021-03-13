# -*- coding: utf-8 -*-
# © 2015 Comunitea
# © 2021 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields


class CrmClaimTemplate(models.Model):
    _name = 'crm.claim.template'
    _order = 'sequence'

    name = fields.Char('Claim template')
    template = fields.Text()
    company_id = fields.Many2one(comodel_name='res.company',
                                 string='Company',
                                 default=lambda rec: rec.env.user.company_id)
    active = fields.Boolean(default=True)
    sequence = fields.Integer()