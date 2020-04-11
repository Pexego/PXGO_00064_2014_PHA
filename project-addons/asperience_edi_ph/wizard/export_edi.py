# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api


class ExportEdiWzd(models.TransientModel):
    _inherit = 'export.edi.wzd'

    @api.multi
    def export(self):
        res = super(ExportEdiWzd, self).export()
        # Generate invoice attachments after export
        if self.env.context['active_model'] == 'account.invoice':
            invoice_ids = self.env['account.invoice'].\
                    browse(self.env.context['active_ids'])
            self.env['report'].get_pdf(invoice_ids, 'account.report_invoice')
        return res
