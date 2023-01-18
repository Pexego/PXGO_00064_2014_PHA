# -*- coding: utf-8 -*-
# © 2023 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, fields, api, _
from openerp.exceptions import Warning
from openerp.modules.registry import RegistryManager
import datetime

class StockInvoiceOnShipping(models.TransientModel):
    _inherit = 'stock.invoice.onshipping'

    _defaults = {
        'invoice_date':
            lambda *a: datetime.date.today() - datetime.timedelta(days=1),
    }

    @api.multi
    def open_invoice_step_by_step(self):
        active_ids = self.env.context.get('active_ids')
        invoice_ids = []
        for id in active_ids:
            with api.Environment.manage():
                new_cr = RegistryManager.get(self.env.cr.dbname).cursor()
                # Create a new environment with new cursor database
                new_env = api.Environment(new_cr, self.env.uid,
                                          self.env.context)
                invoice_id = self.with_env(new_env).\
                    with_context(active_ids=[id]).create_invoice()
                new_cr.commit()
                new_cr.close()
                invoice_ids += invoice_id if invoice_id else []

        if invoice_ids == []:
            raise Warning(_('Error!'), _('No invoice created!'))

        journal2type = {'sale': 'out_invoice',
                        'purchase': 'in_invoice',
                        'sale_refund': 'out_refund',
                        'purchase_refund': 'in_refund'}
        inv_type = journal2type.get(self.journal_type) or 'out_invoice'
        if inv_type == 'out_invoice':
            action_obj = self.env.ref('account.action_invoice_tree1')
        elif inv_type == 'in_invoice':
            action_obj = self.env.ref('account.action_invoice_tree2')
        elif inv_type == 'out_refund':
            action_obj = self.env.ref('account.action_invoice_tree3')
        elif inv_type == 'in_refund':
            action_obj = self.env.ref('account.action_invoice_tree4')
        else:
            return True

        action = action_obj.read()[0]
        action['domain'] = "[('id','in', " + str(invoice_ids) + ")]"
        return action
