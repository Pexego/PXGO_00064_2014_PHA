# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, exceptions, _
from ..validations import is_valid_email, is_valid_fax

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def send_email(self):
        message_type = 'email'
        if self.transfer and self.env.context.get('transfer_button', False):
            mail = self.notified_partner_id.transfer_sales_mail
            fax = self.notified_partner_id.clean_fax_number
            if is_valid_email(mail):
                if self.state in ('draft', 'sent'):
                    template_id = self.env. \
                        ref('mail_ph.sale_transfer_budget_mail_template')
                else:
                    template_id = self.env. \
                        ref('mail_ph.sale_transfer_order_mail_template')
            elif is_valid_fax(fax):
                message_type = 'fax'
                if self.state in ('draft', 'sent'):
                    template_id = self.env. \
                        ref('mail_ph.sale_transfer_budget_fax_template')
                else:
                    template_id = self.env. \
                        ref('mail_ph.sale_transfer_order_fax_template')
            else:
                raise exceptions.ValidationError(
                    _('Not valid email or fax number configured for ') +
                      self.notified_partner_id.name)
        else:
            message = _('No valid email configured for shipping partner or '
                        'its parent')
            mail = self.partner_shipping_id.sales_mail
            parent_mail = self.partner_shipping_id.parent_id.sales_mail
            email_string = mail if mail else parent_mail
            if not is_valid_email(email_string):
                raise exceptions.ValidationError(message)

            if self.state in ('draft', 'sent'):
                template_id = self.env.\
                    ref('mail_ph.sale_budget_mail_template')
            else:
                template_id = self.env.\
                    ref('mail_ph.sale_order_mail_template')

        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='sale.order',
            default_res_id=self.id,
            default_use_template=bool(template_id),
            default_template_id=template_id and template_id.id or False,
            default_composition_mode='mass_mail'
        )
        return {
            'name': _('Compose {}').format(message_type),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
