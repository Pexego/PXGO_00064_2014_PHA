# -*- coding: utf-8 -*-
# © 2020 Pharmadus I.T.
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from openerp import models, api, exceptions, _
from ..validations import is_valid_email


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.multi
    def send_email(self):
        self.ensure_one()

        message = _('No valid email configured for this partner or '
                    'its parent')
        mail = self.partner_id.sales_mail
        parent_mail = self.partner_id.parent_id.sales_mail
        if not mail and not parent_mail:
            raise exceptions.ValidationError(message)

        email_string = mail if mail else parent_mail
        if not is_valid_email(email_string):
            raise exceptions.ValidationError(message)

        if self.state in ('draft', 'sent'):
            template_id = self.env.\
                ref('mail_ph.purchase_quotation_mail_template')
        else:
            template_id = self.env.\
                ref('mail_ph.purchase_order_mail_template')

        compose_form = self.env.ref(
            'mail.email_compose_message_wizard_form', False)
        ctx = dict(
            default_model='purchase.order',
            default_res_id=self.id,
            default_use_template=bool(template_id),
            default_template_id=template_id and template_id.id or False,
            default_composition_mode='comment'
        )
        return {
            'name': _('Compose e-mail'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'mail.compose.message',
            'views': [(compose_form.id, 'form')],
            'view_id': compose_form.id,
            'target': 'new',
            'context': ctx,
        }
