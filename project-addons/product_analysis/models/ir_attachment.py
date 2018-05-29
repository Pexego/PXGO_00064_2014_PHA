# -*- coding: utf-8 -*-
# © 2018 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        model = vals.get('res_model', False)
        if model == 'stock.production.lot':
            attachment_id = self.search([
                ('res_model', '=', model),
                ('res_id', '=', vals.get('res_id')),
                ('name', '=', vals.get('name'))  # If same name, overwrite it
            ])
            if attachment_id:
                attachment_id.write({'datas': vals.get('datas')})
                res = attachment_id
            else:
                res = super(IrAttachment, self).create(vals)
        else:
            res = super(IrAttachment, self).create(vals)
        return res
