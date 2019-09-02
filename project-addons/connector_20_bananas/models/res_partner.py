# -*- coding: utf-8 -*-
# © 2019 Comunitea
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from openerp import models, fields


class ResPartner(models.Model):

    _inherit = 'res.partner'

    bananas_synchronized = fields.Boolean('Synchronized with 20 bananas')
