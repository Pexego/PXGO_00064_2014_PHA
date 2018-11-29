# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api


class CreateEan13Wizard(models.TransientModel):
    _name = 'create.ean13.wizard'

    ean13 = fields.Char(required=True)

    @api.multi
    def create_ean13(self):
        self.env['ean13.international'].create({'name': self.ean13})
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }