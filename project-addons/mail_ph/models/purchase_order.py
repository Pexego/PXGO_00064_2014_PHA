# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, exceptions, _
from ..validations import is_valid_email


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def send_email(self):
        for purchase_id in self:
            message = _('No valid email configured for this partner or '
                        'its parent')
            mail = purchase_id.partner_id.sales_mail
            parent_mail = purchase_id.partner_id.parent_id.sales_mail
            if not mail and not parent_mail:
                raise exceptions.ValidationError(message)

            email_string = mail if mail else parent_mail
            if not is_valid_email(email_string):
                raise exceptions.ValidationError(message)

            if purchase_id.state in ('draft', 'sent'):
                template_id = self.env.\
                    ref('mail_ph.purchase_quotation_mail_template')
            else:
                template_id = self.env.\
                    ref('mail_ph.purchase_order_mail_template')
            template_id.send_mail(purchase_id.id, force_send=True)
            raise exceptions.Warning(_('Successfully sent email'))
