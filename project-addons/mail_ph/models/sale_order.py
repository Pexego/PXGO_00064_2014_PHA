# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, exceptions, _
from ..validations import is_valid_email, is_valid_fax

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def send_email(self):
        for sale_id in self:
            message_type = 'email'
            if sale_id.transfer:
                mail = sale_id.notified_partner_id.transfer_sales_mail
                fax = sale_id.notified_partner_id.clean_fax_number
                if is_valid_email(mail):
                    if sale_id.state in ('draft', 'sent'):
                        template_id = self.env. \
                            ref('mail_ph.sale_transfer_budget_mail_template')
                    else:
                        template_id = self.env. \
                            ref('mail_ph.sale_transfer_order_mail_template')
                elif is_valid_fax(fax):
                    message_type = 'fax'
                    if sale_id.state in ('draft', 'sent'):
                        template_id = self.env. \
                            ref('mail_ph.sale_transfer_budget_fax_template')
                    else:
                        template_id = self.env. \
                            ref('mail_ph.sale_transfer_order_fax_template')
                else:
                    raise exceptions.ValidationError(
                        _('Not valid email or fax number configured for ') +
                          sale_id.notified_partner_id.name)
            else:
                message = _('No valid email configured for shipping partner or '
                            'its parent')
                mail = sale_id.partner_shipping_id.sales_mail
                parent_mail = sale_id.partner_shipping_id.parent_id.sales_mail
                email_string = mail if mail else parent_mail
                if not is_valid_email(email_string):
                    raise exceptions.ValidationError(message)

                if sale_id.state in ('draft', 'sent'):
                    template_id = self.env.\
                        ref('mail_ph.sale_budget_mail_template')
                else:
                    template_id = self.env.\
                        ref('mail_ph.sale_order_mail_template')

            template_id.send_mail(sale_id.id, force_send=True)
            raise exceptions.Warning(_('Successfully sent {}').
                                     format(message_type))
